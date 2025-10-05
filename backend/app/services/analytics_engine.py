"""
Analytics Engine for SAR Mission Commander
Provides performance metrics, reporting, and data analysis
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import func, and_, desc
import json

from ..core.database import get_db
from ..models.mission import Mission, MissionStatus
from ..models.drone import Drone
from ..models.discovery import Discovery
from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class MissionMetrics:
    mission_id: str
    total_time_minutes: float
    area_covered_km2: float
    discoveries_found: int
    drones_used: int
    efficiency_score: float
    success_rate: float
    avg_drone_utilization: float
    cost_estimate: float

@dataclass
class SystemMetrics:
    total_missions: int
    active_missions: int
    completed_missions: int
    total_discoveries: int
    avg_mission_duration: float
    system_uptime: float
    drone_fleet_size: int
    active_drones: int
    total_flight_hours: float

@dataclass
class PerformanceReport:
    period_start: datetime
    period_end: datetime
    mission_metrics: List[MissionMetrics]
    system_metrics: SystemMetrics
    trends: Dict[str, Any]
    recommendations: List[str]

class AnalyticsEngine:
    """Provides analytics and reporting capabilities"""
    
    def __init__(self):
        self._running = False
        self.cached_metrics: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def start(self):
        """Start the analytics engine"""
        self._running = True
        logger.info("Analytics Engine started")
        
        # Start background tasks
        asyncio.create_task(self._update_cached_metrics())
        
    async def stop(self):
        """Stop the analytics engine"""
        self._running = False
        logger.info("Analytics Engine stopped")
    
    async def get_mission_analytics(self, mission_id: str) -> Optional[MissionMetrics]:
        """Get detailed analytics for a specific mission"""
        try:
            with get_db_session() as db:
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    return None
                
                # Calculate mission duration
                start_time = mission.start_time or mission.created_at
                end_time = mission.end_time or datetime.utcnow()
                duration = (end_time - start_time).total_seconds() / 60
                
                # Get discoveries for this mission
                discoveries = db.query(Discovery).filter(Discovery.mission_id == mission_id).count()
                
                # Calculate efficiency score (simplified)
                efficiency_score = 0.0
                if mission.area_covered and mission.time_limit_minutes:
                    coverage_rate = mission.area_covered / (duration / 60)  # km2 per hour
                    efficiency_score = min(coverage_rate / 10, 1.0)  # Normalize to 0-1
                
                # Calculate success rate
                success_rate = 1.0 if mission.status == MissionStatus.COMPLETED else 0.0
                if mission.status == MissionStatus.ACTIVE and duration > 30:
                    success_rate = 0.7  # Partial success for active long-running missions
                
                # Estimate cost (simplified)
                cost_estimate = duration * 10  # $10 per minute of operation
                
                return MissionMetrics(
                    mission_id=mission_id,
                    total_time_minutes=duration,
                    area_covered_km2=mission.area_covered or 0.0,
                    discoveries_found=discoveries,
                    drones_used=mission.max_drones or 1,
                    efficiency_score=efficiency_score,
                    success_rate=success_rate,
                    avg_drone_utilization=min(duration / (mission.max_drones or 1), 1.0),
                    cost_estimate=cost_estimate
                )
                
        except Exception as e:
            logger.error(f"Failed to get mission analytics: {e}")
            return None
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Get overall system metrics"""
        try:
            cache_key = "system_metrics"
            if cache_key in self.cached_metrics:
                cached_data, timestamp = self.cached_metrics[cache_key]
                if (datetime.utcnow() - timestamp).total_seconds() < self.cache_ttl:
                    return cached_data
            
            with get_db_session() as db:
                # Mission statistics
                total_missions = db.query(Mission).count()
                active_missions = db.query(Mission).filter(Mission.status == MissionStatus.ACTIVE).count()
                completed_missions = db.query(Mission).filter(Mission.status == MissionStatus.COMPLETED).count()
                
                # Discovery statistics
                total_discoveries = db.query(Discovery).count()
                
                # Average mission duration
                completed_missions_with_duration = db.query(Mission).filter(
                    and_(
                        Mission.status == MissionStatus.COMPLETED,
                        Mission.start_time.isnot(None),
                        Mission.end_time.isnot(None)
                    )
                ).all()
                
                avg_duration = 0.0
                if completed_missions_with_duration:
                    total_duration = sum([
                        (mission.end_time - mission.start_time).total_seconds() / 60
                        for mission in completed_missions_with_duration
                    ])
                    avg_duration = total_duration / len(completed_missions_with_duration)
                
                # Drone statistics (mock data - would come from drone manager in real implementation)
                drone_fleet_size = 5  # This would be dynamic
                active_drones = 3  # This would be dynamic
                
                # Total flight hours (mock calculation)
                total_flight_hours = sum([
                    (mission.end_time - mission.start_time).total_seconds() / 3600
                    for mission in completed_missions_with_duration
                ])
                
                metrics = SystemMetrics(
                    total_missions=total_missions,
                    active_missions=active_missions,
                    completed_missions=completed_missions,
                    total_discoveries=total_discoveries,
                    avg_mission_duration=avg_duration,
                    system_uptime=99.9,  # Mock uptime
                    drone_fleet_size=drone_fleet_size,
                    active_drones=active_drones,
                    total_flight_hours=total_flight_hours
                )
                
                # Cache the results
                self.cached_metrics[cache_key] = (metrics, datetime.utcnow())
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0.0, 0.0, 0, 0, 0.0)
    
    async def get_performance_report(self, days: int = 30) -> PerformanceReport:
        """Generate a performance report for the specified period"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            with get_db_session() as db:
                # Get missions in the period
                missions = db.query(Mission).filter(
                    and_(
                        Mission.created_at >= start_date,
                        Mission.created_at <= end_date
                    )
                ).all()
                
                # Calculate mission metrics
                mission_metrics = []
                for mission in missions:
                    metrics = await self.get_mission_analytics(mission.id)
                    if metrics:
                        mission_metrics.append(metrics)
                
                # Get system metrics
                system_metrics = await self.get_system_metrics()
                
                # Calculate trends
                trends = await self._calculate_trends(start_date, end_date)
                
                # Generate recommendations
                recommendations = await self._generate_recommendations(mission_metrics, system_metrics)
                
                return PerformanceReport(
                    period_start=start_date,
                    period_end=end_date,
                    mission_metrics=mission_metrics,
                    system_metrics=system_metrics,
                    trends=trends,
                    recommendations=recommendations
                )
                
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return PerformanceReport(
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                mission_metrics=[],
                system_metrics=SystemMetrics(0, 0, 0, 0, 0.0, 0.0, 0, 0, 0.0),
                trends={},
                recommendations=["Unable to generate report"]
            )
    
    async def get_discovery_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics about discoveries"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            with get_db_session() as db:
                # Get discoveries in the period
                discoveries = db.query(Discovery).filter(
                    and_(
                        Discovery.timestamp >= start_date,
                        Discovery.timestamp <= end_date
                    )
                ).all()
                
                # Analyze discovery types
                discovery_types = {}
                confidence_scores = []
                
                for discovery in discoveries:
                    discovery_type = discovery.type
                    discovery_types[discovery_type] = discovery_types.get(discovery_type, 0) + 1
                    confidence_scores.append(discovery.confidence)
                
                # Calculate statistics
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                
                return {
                    "total_discoveries": len(discoveries),
                    "discovery_types": discovery_types,
                    "average_confidence": avg_confidence,
                    "high_confidence_discoveries": len([d for d in discoveries if d.confidence > 0.8]),
                    "verified_discoveries": len([d for d in discoveries if d.status == "verified"]),
                    "period_days": days
                }
                
        except Exception as e:
            logger.error(f"Failed to get discovery analytics: {e}")
            return {"error": str(e)}
    
    async def get_drone_performance(self, drone_id: Optional[str] = None) -> Dict[str, Any]:
        """Get drone performance analytics"""
        try:
            with get_db_session() as db:
                # Get missions involving the drone
                if drone_id:
                    # In a real implementation, we'd have a drone-mission relationship table
                    missions = db.query(Mission).all()  # Simplified - would filter by drone
                else:
                    missions = db.query(Mission).all()
                
                # Calculate performance metrics
                total_missions = len(missions)
                successful_missions = len([m for m in missions if m.status == MissionStatus.COMPLETED])
                success_rate = successful_missions / total_missions if total_missions > 0 else 0
                
                # Calculate average mission time
                completed_missions = [m for m in missions if m.status == MissionStatus.COMPLETED and m.start_time and m.end_time]
                avg_mission_time = 0
                if completed_missions:
                    total_time = sum([
                        (m.end_time - m.start_time).total_seconds() / 60
                        for m in completed_missions
                    ])
                    avg_mission_time = total_time / len(completed_missions)
                
                return {
                    "drone_id": drone_id or "all",
                    "total_missions": total_missions,
                    "successful_missions": successful_missions,
                    "success_rate": success_rate,
                    "average_mission_time_minutes": avg_mission_time,
                    "total_flight_hours": sum([
                        (m.end_time - m.start_time).total_seconds() / 3600
                        for m in completed_missions
                    ])
                }
                
        except Exception as e:
            logger.error(f"Failed to get drone performance: {e}")
            return {"error": str(e)}
    
    async def get_mission_success_rates(self, days: int = 30) -> Dict[str, float]:
        """Get mission success rates by type"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            with get_db_session() as db:
                missions = db.query(Mission).filter(
                    and_(
                        Mission.created_at >= start_date,
                        Mission.created_at <= end_date
                    )
                ).all()
                
                # Group by mission type
                mission_types = {}
                for mission in missions:
                    mission_type = mission.mission_type
                    if mission_type not in mission_types:
                        mission_types[mission_type] = {"total": 0, "completed": 0}
                    
                    mission_types[mission_type]["total"] += 1
                    if mission.status == MissionStatus.COMPLETED:
                        mission_types[mission_type]["completed"] += 1
                
                # Calculate success rates
                success_rates = {}
                for mission_type, stats in mission_types.items():
                    success_rate = stats["completed"] / stats["total"] if stats["total"] > 0 else 0
                    success_rates[mission_type] = success_rate
                
                return success_rates
                
        except Exception as e:
            logger.error(f"Failed to get mission success rates: {e}")
            return {}
    
    async def _calculate_trends(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate trends over the specified period"""
        try:
            with get_db_session() as db:
                # Calculate daily mission counts
                daily_missions = {}
                current_date = start_date
                
                while current_date <= end_date:
                    next_date = current_date + timedelta(days=1)
                    
                    count = db.query(Mission).filter(
                        and_(
                            Mission.created_at >= current_date,
                            Mission.created_at < next_date
                        )
                    ).count()
                    
                    daily_missions[current_date.strftime("%Y-%m-%d")] = count
                    current_date = next_date
                
                # Calculate trends
                mission_counts = list(daily_missions.values())
                
                # Simple trend calculation (increasing/decreasing)
                trend_direction = "stable"
                if len(mission_counts) >= 2:
                    first_half = mission_counts[:len(mission_counts)//2]
                    second_half = mission_counts[len(mission_counts)//2:]
                    
                    first_avg = sum(first_half) / len(first_half) if first_half else 0
                    second_avg = sum(second_half) / len(second_half) if second_half else 0
                    
                    if second_avg > first_avg * 1.1:
                        trend_direction = "increasing"
                    elif second_avg < first_avg * 0.9:
                        trend_direction = "decreasing"
                
                return {
                    "mission_trend": trend_direction,
                    "daily_missions": daily_missions,
                    "total_missions_period": sum(mission_counts),
                    "average_daily_missions": sum(mission_counts) / len(mission_counts) if mission_counts else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            return {}
    
    async def _generate_recommendations(self, mission_metrics: List[MissionMetrics], system_metrics: SystemMetrics) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        try:
            # Analyze mission efficiency
            if mission_metrics:
                avg_efficiency = sum([m.efficiency_score for m in mission_metrics]) / len(mission_metrics)
                
                if avg_efficiency < 0.5:
                    recommendations.append("Mission efficiency is low - consider optimizing search patterns")
                elif avg_efficiency > 0.8:
                    recommendations.append("Mission efficiency is excellent - current patterns are optimal")
                
                # Analyze success rates
                avg_success_rate = sum([m.success_rate for m in mission_metrics]) / len(mission_metrics)
                if avg_success_rate < 0.7:
                    recommendations.append("Mission success rate is below target - review operational procedures")
                
                # Analyze cost efficiency
                avg_cost = sum([m.cost_estimate for m in mission_metrics]) / len(mission_metrics)
                if avg_cost > 1000:  # $1000 threshold
                    recommendations.append("Mission costs are high - consider optimizing resource allocation")
            
            # Analyze system metrics
            if system_metrics.total_missions > 0:
                completion_rate = system_metrics.completed_missions / system_metrics.total_missions
                if completion_rate < 0.8:
                    recommendations.append("System completion rate is low - investigate mission failures")
                
                if system_metrics.avg_mission_duration > 120:  # 2 hours
                    recommendations.append("Average mission duration is long - consider mission planning optimization")
            
            # Drone utilization
            if system_metrics.drone_fleet_size > 0:
                utilization_rate = system_metrics.active_drones / system_metrics.drone_fleet_size
                if utilization_rate < 0.5:
                    recommendations.append("Drone fleet utilization is low - consider scaling down or increasing missions")
                elif utilization_rate > 0.9:
                    recommendations.append("Drone fleet utilization is high - consider expanding fleet capacity")
            
            # Discovery effectiveness
            if system_metrics.total_discoveries > 0 and system_metrics.completed_missions > 0:
                discoveries_per_mission = system_metrics.total_discoveries / system_metrics.completed_missions
                if discoveries_per_mission < 0.5:
                    recommendations.append("Discovery rate is low - consider improving detection algorithms")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations"]
    
    async def _update_cached_metrics(self):
        """Background task to update cached metrics"""
        while self._running:
            try:
                # Update system metrics cache
                await self.get_system_metrics()
                
                # Clean up old cache entries
                current_time = datetime.utcnow()
                expired_keys = []
                
                for key, (data, timestamp) in self.cached_metrics.items():
                    if (current_time - timestamp).total_seconds() > self.cache_ttl * 2:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.cached_metrics[key]
                
                await asyncio.sleep(self.cache_ttl)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error updating cached metrics: {e}")
                await asyncio.sleep(self.cache_ttl)

# Global analytics engine instance
analytics_engine = AnalyticsEngine()