"""
Drone service layer for drone management and communication.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import asyncio

from ..models.drone import Drone, DroneStatus, DroneType, DroneCapabilities
from ..core.config import settings

class DroneService:
    """Service for drone management operations."""
    
    def __init__(self):
        self.active_commands: Dict[str, Dict[str, Any]] = {}  # Track active commands
        self.telemetry_streams: Dict[str, Dict[str, Any]] = {}  # Track telemetry streams
    
    async def get_drones(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        drone_type: Optional[str] = None,
        available_only: bool = False
    ) -> List[Drone]:
        """Get list of drones with optional filtering."""
        query = db.query(Drone)
        
        if status:
            try:
                status_enum = DroneStatus(status)
                query = query.filter(Drone.status == status_enum)
            except ValueError:
                pass
        
        if drone_type:
            try:
                type_enum = DroneType(drone_type)
                query = query.filter(Drone.drone_type == type_enum)
            except ValueError:
                pass
        
        if available_only:
            query = query.filter(
                and_(
                    Drone.status == DroneStatus.IDLE,
                    Drone.maintenance_due == False,
                    Drone.assigned_mission_id.is_(None)
                )
            )
        
        return query.order_by(Drone.name).offset(skip).limit(limit).all()
    
    async def get_drone_by_id(self, db: Session, drone_id: str) -> Optional[Drone]:
        """Get a drone by its ID."""
        return db.query(Drone).filter(Drone.drone_id == drone_id).first()
    
    async def register_drone(self, db: Session, drone_data: Dict[str, Any]) -> Drone:
        """Register a new drone in the fleet."""
        drone = Drone(
            drone_id=drone_data["drone_id"],
            name=drone_data["name"],
            model=drone_data["model"],
            serial_number=drone_data["serial_number"],
            drone_type=DroneType(drone_data["drone_type"]),
            manufacturer=drone_data.get("manufacturer"),
            firmware_version=drone_data.get("firmware_version"),
            status=DroneStatus.OFFLINE,
            
            # Set home location if provided
            home_latitude=drone_data.get("home_latitude"),
            home_longitude=drone_data.get("home_longitude"),
            home_altitude=drone_data.get("home_altitude", 0.0),
            
            # Initialize capabilities
            capabilities=drone_data.get("capabilities", {}),
            max_payload_kg=drone_data.get("max_payload_kg", 2.0),
            
            # Initialize health metrics
            health_score=1.0,
            maintenance_due=False
        )
        
        db.add(drone)
        db.commit()
        db.refresh(drone)
        
        # Create capabilities record if provided
        if "detailed_capabilities" in drone_data:
            await self._create_capabilities_record(db, drone.drone_id, drone_data["detailed_capabilities"])
        
        return drone
    
    async def update_drone(self, db: Session, drone_id: str, update_data: Dict[str, Any]) -> Optional[Drone]:
        """Update drone information and status."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone:
            return None
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(drone, field):
                if field == "status" and isinstance(value, str):
                    try:
                        setattr(drone, field, DroneStatus(value))
                    except ValueError:
                        continue
                elif field == "drone_type" and isinstance(value, str):
                    try:
                        setattr(drone, field, DroneType(value))
                    except ValueError:
                        continue
                else:
                    setattr(drone, field, value)
        
        drone.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(drone)
        
        return drone
    
    async def update_telemetry(self, db: Session, drone_id: str, telemetry_data: Dict[str, Any]) -> bool:
        """Update drone telemetry and heartbeat."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone:
            return False
        
        # Update location if provided
        if all(key in telemetry_data for key in ["latitude", "longitude", "altitude"]):
            drone.update_location(
                telemetry_data["latitude"],
                telemetry_data["longitude"],
                telemetry_data["altitude"]
            )
        
        # Update battery if provided
        if "battery_percentage" in telemetry_data:
            drone.update_battery(
                telemetry_data["battery_percentage"],
                telemetry_data.get("battery_voltage"),
                telemetry_data.get("battery_current")
            )
        
        # Update flight dynamics
        for field in ["heading_degrees", "ground_speed_ms", "vertical_speed_ms", 
                     "wind_speed_ms", "wind_direction_degrees"]:
            if field in telemetry_data:
                setattr(drone, field, telemetry_data[field])
        
        # Update environmental sensors
        for field in ["ambient_temperature", "humidity_percentage", "barometric_pressure"]:
            if field in telemetry_data:
                setattr(drone, field, telemetry_data[field])
        
        # Update communication metrics
        for field in ["signal_strength", "data_link_quality", "video_link_quality"]:
            if field in telemetry_data:
                setattr(drone, field, telemetry_data[field])
        
        # Update heartbeat
        drone.last_heartbeat = datetime.utcnow()
        
        # Update status based on telemetry
        await self._update_status_from_telemetry(drone, telemetry_data)
        
        db.commit()
        return True
    
    async def send_command(
        self,
        db: Session,
        drone_id: str,
        command: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a command to a drone."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone:
            raise ValueError("Drone not found")
        
        if not drone.is_operational():
            raise ValueError("Drone is not operational")
        
        # Generate command ID
        command_id = f"CMD_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Store command for tracking
        self.active_commands[command_id] = {
            "drone_id": drone_id,
            "command": command,
            "parameters": parameters,
            "sent_at": datetime.utcnow(),
            "status": "sent",
            "retries": 0
        }
        
        # Execute command based on type
        result = await self._execute_command(drone, command, parameters, command_id)
        
        return {
            "command_id": command_id,
            "status": "sent",
            "result": result
        }
    
    async def get_drone_status(self, db: Session, drone_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time drone status and telemetry."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone:
            return None
        
        return {
            "drone_id": drone.drone_id,
            "status": drone.status.value,
            "location": {
                "latitude": drone.current_latitude,
                "longitude": drone.current_longitude,
                "altitude": drone.current_altitude,
                "heading": drone.heading_degrees
            } if drone.current_latitude else None,
            "battery": {
                "percentage": drone.battery_percentage,
                "voltage": drone.battery_voltage,
                "remaining_time_minutes": drone.remaining_flight_time_minutes
            },
            "flight_dynamics": {
                "ground_speed_ms": drone.ground_speed_ms,
                "vertical_speed_ms": drone.vertical_speed_ms,
                "wind_speed_ms": drone.wind_speed_ms,
                "wind_direction_degrees": drone.wind_direction_degrees
            },
            "mission": {
                "assigned_mission_id": drone.assigned_mission_id,
                "current_task": drone.current_task,
                "progress": drone.task_progress_percentage
            },
            "health": {
                "score": drone.health_score,
                "maintenance_due": drone.maintenance_due,
                "last_error": drone.last_error
            },
            "communication": {
                "signal_strength": drone.signal_strength,
                "data_link_quality": drone.data_link_quality,
                "video_link_quality": drone.video_link_quality,
                "last_heartbeat": drone.last_heartbeat.isoformat() if drone.last_heartbeat else None
            },
            "environment": {
                "temperature": drone.ambient_temperature,
                "humidity": drone.humidity_percentage,
                "pressure": drone.barometric_pressure
            }
        }
    
    async def check_health(self, db: Session, drone_id: str) -> Optional[Dict[str, Any]]:
        """Perform comprehensive health check on drone."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone:
            return None
        
        health_issues = []
        critical_alerts = []
        
        # Check battery health
        if drone.battery_percentage and drone.battery_percentage < settings.emergency_return_battery:
            critical_alerts.append({
                "type": "low_battery",
                "message": f"Battery critically low: {drone.battery_percentage}%",
                "severity": "critical"
            })
        elif drone.battery_percentage and drone.battery_percentage < settings.min_battery_level:
            health_issues.append("Battery level below minimum threshold")
        
        # Check communication
        if drone.last_heartbeat:
            time_since_heartbeat = (datetime.utcnow() - drone.last_heartbeat).total_seconds()
            if time_since_heartbeat > 30:  # 30 seconds without heartbeat
                critical_alerts.append({
                    "type": "communication_loss",
                    "message": f"No heartbeat for {time_since_heartbeat:.0f} seconds",
                    "severity": "critical"
                })
        
        # Check signal strength
        if drone.signal_strength and drone.signal_strength < -80:  # dBm
            health_issues.append("Weak signal strength")
        
        # Check environmental conditions
        if drone.wind_speed_ms and drone.wind_speed_ms > settings.max_wind_speed:
            health_issues.append(f"Wind speed exceeds safe limits: {drone.wind_speed_ms} m/s")
        
        # Calculate overall health score
        health_score = drone.health_score
        if critical_alerts:
            health_score = min(health_score, 0.3)
        elif health_issues:
            health_score = min(health_score, 0.7)
        
        return {
            "drone_id": drone_id,
            "overall_health": health_score,
            "status": "critical" if critical_alerts else "warning" if health_issues else "healthy",
            "health_issues": health_issues,
            "critical_alerts": critical_alerts,
            "recommendations": self._generate_health_recommendations(drone, health_issues, critical_alerts),
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def assign_to_mission(
        self,
        db: Session,
        drone_id: str,
        mission_id: str,
        task: str = "search"
    ) -> Optional[Drone]:
        """Assign a drone to a mission."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone or not drone.is_available():
            return None
        
        drone.set_mission(mission_id, task)
        drone.status = DroneStatus.PREFLIGHT
        
        db.commit()
        db.refresh(drone)
        
        return drone
    
    async def unassign_from_mission(self, db: Session, drone_id: str) -> Optional[Drone]:
        """Unassign a drone from its current mission."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone:
            return None
        
        drone.clear_mission()
        if drone.status in [DroneStatus.PREFLIGHT, DroneStatus.ACTIVE]:
            drone.status = DroneStatus.IDLE
        
        db.commit()
        db.refresh(drone)
        
        return drone
    
    async def emergency_return(
        self,
        db: Session,
        drone_id: str,
        emergency_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Command drone to perform emergency return to home."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone:
            return None
        
        # Send return to home command
        command_result = await self.send_command(
            db, drone_id, "return_to_home", {
                "emergency": True,
                "reason": emergency_data.get("reason", "Emergency return"),
                "priority": "critical"
            }
        )
        
        # Update drone status
        drone.status = DroneStatus.RETURNING
        drone.last_error = emergency_data.get("reason", "Emergency return initiated")
        
        db.commit()
        
        # Estimate return time
        distance_to_home = drone.get_distance_from_home()
        if distance_to_home and drone.ground_speed_ms:
            estimated_return_time = distance_to_home / drone.ground_speed_ms / 60  # minutes
        else:
            estimated_return_time = 10  # Default estimate
        
        return {
            "command_id": command_result["command_id"],
            "estimated_return_time": estimated_return_time,
            "distance_to_home": distance_to_home,
            "current_battery": drone.battery_percentage
        }
    
    async def get_capabilities(self, db: Session, drone_id: str) -> Optional[Dict[str, Any]]:
        """Get drone capabilities and specifications."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone:
            return None
        
        # Get detailed capabilities if available
        capabilities_record = db.query(DroneCapabilities).filter(
            DroneCapabilities.drone_id == drone_id
        ).first()
        
        if capabilities_record:
            return capabilities_record.to_dict()
        
        # Return basic capabilities from drone record
        return drone.capabilities or {}
    
    async def schedule_maintenance(
        self,
        db: Session,
        drone_id: str,
        maintenance_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Schedule maintenance for a drone."""
        drone = await self.get_drone_by_id(db, drone_id)
        if not drone:
            return None
        
        maintenance_date = maintenance_data.get("scheduled_date")
        if isinstance(maintenance_date, str):
            maintenance_date = datetime.fromisoformat(maintenance_date)
        
        drone.next_maintenance = maintenance_date
        drone.maintenance_due = maintenance_data.get("immediate", False)
        
        if drone.maintenance_due:
            drone.status = DroneStatus.MAINTENANCE
        
        db.commit()
        
        return {
            "maintenance_date": maintenance_date.isoformat() if maintenance_date else None,
            "immediate": drone.maintenance_due,
            "status": drone.status.value
        }
    
    async def get_mission_history(
        self,
        db: Session,
        drone_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get drone's mission history."""
        # This would typically query a mission history table
        # Placeholder implementation
        return [
            {
                "mission_id": "SAR_20231201_140000",
                "start_time": "2023-12-01T14:00:00Z",
                "end_time": "2023-12-01T16:30:00Z",
                "flight_time_minutes": 150,
                "discoveries": 2,
                "status": "completed"
            }
        ]
    
    async def get_fleet_status(self, db: Session) -> Dict[str, Any]:
        """Get overall fleet status and statistics."""
        total_drones = db.query(Drone).count()
        
        status_counts = {}
        for status in DroneStatus:
            count = db.query(Drone).filter(Drone.status == status).count()
            status_counts[status.value] = count
        
        available_drones = db.query(Drone).filter(
            and_(
                Drone.status == DroneStatus.IDLE,
                Drone.maintenance_due == False
            )
        ).count()
        
        maintenance_due = db.query(Drone).filter(Drone.maintenance_due == True).count()
        
        # Calculate average health score
        avg_health = db.query(Drone).filter(
            Drone.health_score.isnot(None)
        ).with_entities(Drone.health_score).all()
        
        avg_health_score = sum(h[0] for h in avg_health) / len(avg_health) if avg_health else 0.0
        
        return {
            "total_drones": total_drones,
            "available_drones": available_drones,
            "status_distribution": status_counts,
            "fleet_health": {
                "average_health_score": avg_health_score,
                "maintenance_due": maintenance_due,
                "operational_percentage": (total_drones - maintenance_due) / max(1, total_drones) * 100
            },
            "active_missions": status_counts.get("active", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_available_drones(
        self,
        db: Session,
        mission_requirements: Optional[Dict[str, Any]] = None
    ) -> List[Drone]:
        """Get drones available for mission assignment."""
        available_drones = await self.get_drones(db, available_only=True)
        
        if not mission_requirements:
            return available_drones
        
        # Filter by mission requirements
        suitable_drones = []
        for drone in available_drones:
            capabilities = await self.get_capabilities(db, drone.drone_id)
            if capabilities and self._check_mission_suitability(capabilities, mission_requirements):
                suitable_drones.append(drone)
        
        return suitable_drones
    
    async def optimize_assignment(
        self,
        db: Session,
        mission_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI-optimized drone assignment recommendations."""
        available_drones = await self.get_available_drones(db, mission_data.get("requirements"))
        
        if not available_drones:
            return {
                "recommendations": [],
                "message": "No suitable drones available"
            }
        
        # Simple optimization based on capabilities and location
        recommendations = []
        for drone in available_drones:
            capabilities = await self.get_capabilities(db, drone.drone_id)
            score = self._calculate_assignment_score(drone, capabilities, mission_data)
            
            recommendations.append({
                "drone_id": drone.drone_id,
                "name": drone.name,
                "suitability_score": score,
                "capabilities": capabilities,
                "current_location": {
                    "latitude": drone.current_latitude,
                    "longitude": drone.current_longitude
                } if drone.current_latitude else None,
                "battery_level": drone.battery_percentage,
                "health_score": drone.health_score
            })
        
        # Sort by suitability score
        recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)
        
        return {
            "recommendations": recommendations,
            "total_available": len(available_drones),
            "optimization_criteria": ["capability_match", "location", "battery_level", "health_score"]
        }
    
    # Private helper methods
    
    async def _create_capabilities_record(
        self,
        db: Session,
        drone_id: str,
        capabilities_data: Dict[str, Any]
    ):
        """Create detailed capabilities record for a drone."""
        capabilities = DroneCapabilities(
            drone_id=drone_id,
            **capabilities_data
        )
        
        db.add(capabilities)
        db.commit()
    
    async def _update_status_from_telemetry(self, drone: Drone, telemetry_data: Dict[str, Any]):
        """Update drone status based on telemetry data."""
        # Auto-update status based on telemetry
        if drone.status == DroneStatus.OFFLINE:
            drone.status = DroneStatus.IDLE
        
        # Check for critical conditions
        if drone.battery_percentage and drone.battery_percentage < settings.emergency_return_battery:
            if drone.status == DroneStatus.ACTIVE:
                drone.status = DroneStatus.RETURNING
    
    async def _execute_command(
        self,
        drone: Drone,
        command: str,
        parameters: Dict[str, Any],
        command_id: str
    ) -> Dict[str, Any]:
        """Execute a command on a drone."""
        # This would typically communicate with the actual drone
        # Placeholder implementation
        
        if command == "takeoff":
            return {"status": "executing", "estimated_duration": 30}
        elif command == "land":
            return {"status": "executing", "estimated_duration": 60}
        elif command == "return_to_home":
            return {"status": "executing", "estimated_duration": 300}
        elif command == "start_mission":
            return {"status": "executing", "mission_started": True}
        elif command == "pause_mission":
            return {"status": "executing", "mission_paused": True}
        else:
            return {"status": "unknown_command", "error": f"Unknown command: {command}"}
    
    def _generate_health_recommendations(
        self,
        drone: Drone,
        health_issues: List[str],
        critical_alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate health-based recommendations."""
        recommendations = []
        
        if critical_alerts:
            for alert in critical_alerts:
                if alert["type"] == "low_battery":
                    recommendations.append("Initiate immediate return to home and landing")
                elif alert["type"] == "communication_loss":
                    recommendations.append("Attempt to re-establish communication link")
        
        if "Battery level below minimum threshold" in health_issues:
            recommendations.append("Plan for battery replacement or charging")
        
        if "Weak signal strength" in health_issues:
            recommendations.append("Move closer to drone or check antenna connections")
        
        if drone.maintenance_due:
            recommendations.append("Schedule maintenance as soon as possible")
        
        return recommendations
    
    def _check_mission_suitability(
        self,
        capabilities: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> bool:
        """Check if drone capabilities meet mission requirements."""
        # Simple capability matching
        if requirements.get("max_altitude") and capabilities.get("flight", {}).get("max_altitude_m", 0) < requirements["max_altitude"]:
            return False
        
        if requirements.get("flight_time") and capabilities.get("flight", {}).get("max_flight_time_minutes", 0) < requirements["flight_time"]:
            return False
        
        if requirements.get("thermal_imaging") and not capabilities.get("imaging", {}).get("thermal", False):
            return False
        
        return True
    
    def _calculate_assignment_score(
        self,
        drone: Drone,
        capabilities: Dict[str, Any],
        mission_data: Dict[str, Any]
    ) -> float:
        """Calculate assignment suitability score."""
        score = 0.0
        
        # Base health and battery score
        score += (drone.health_score or 0.5) * 0.3
        score += (drone.battery_percentage or 50.0) / 100.0 * 0.2
        
        # Capability matching score
        requirements = mission_data.get("requirements", {})
        if self._check_mission_suitability(capabilities, requirements):
            score += 0.3
        
        # Location proximity score (if mission has location)
        mission_location = mission_data.get("location")
        if mission_location and drone.current_latitude and drone.current_longitude:
            # Simple distance-based scoring (would need proper geospatial calculation)
            score += 0.2
        
        return min(1.0, score)