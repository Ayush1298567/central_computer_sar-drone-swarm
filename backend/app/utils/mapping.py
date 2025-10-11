"""
Mapping and Geospatial Utilities for SAR Drone System
Interactive maps, geospatial calculations, and visualization tools
"""
import folium
import plotly.graph_objects as go
import plotly.express as px
import geopandas as gpd
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class SARMappingUtils:
    """Advanced mapping utilities for SAR operations"""
    
    def __init__(self):
        self.default_center = [47.3769, 8.5417]  # Zurich, Switzerland
        self.default_zoom = 10
        
    def create_mission_map(self, 
                          mission_data: Dict[str, Any],
                          telemetry_data: List[Dict[str, Any]] = None,
                          discoveries: List[Dict[str, Any]] = None) -> str:
        """Create interactive Folium map for mission visualization"""
        
        try:
            # Create base map
            m = folium.Map(
                location=self.default_center,
                zoom_start=self.default_zoom,
                tiles='OpenStreetMap'
            )
            
            # Add mission center
            if mission_data.get('center_lat') and mission_data.get('center_lng'):
                folium.Marker(
                    [mission_data['center_lat'], mission_data['center_lng']],
                    popup=f"Mission Center: {mission_data.get('name', 'Unknown')}",
                    icon=folium.Icon(color='blue', icon='home')
                ).add_to(m)
            
            # Add search area polygon
            if mission_data.get('search_area'):
                search_coords = mission_data['search_area']
                folium.Polygon(
                    locations=[[coord['lat'], coord['lng']] for coord in search_coords],
                    color='blue',
                    weight=2,
                    fillColor='lightblue',
                    fillOpacity=0.3,
                    popup=f"Search Area: {mission_data.get('name', 'Unknown')}"
                ).add_to(m)
            
            # Add drone tracks
            if telemetry_data:
                drone_tracks = self._group_telemetry_by_drone(telemetry_data)
                colors = ['red', 'green', 'orange', 'purple', 'darkred', 'lightred']
                
                for i, (drone_id, track_data) in enumerate(drone_tracks.items()):
                    color = colors[i % len(colors)]
                    
                    # Add track line
                    folium.PolyLine(
                        locations=[[point['lat'], point['lng']] for point in track_data],
                        color=color,
                        weight=3,
                        opacity=0.7,
                        popup=f"Drone {drone_id} Track"
                    ).add_to(m)
                    
                    # Add current position
                    if track_data:
                        latest_point = track_data[-1]
                        folium.CircleMarker(
                            [latest_point['lat'], latest_point['lng']],
                            radius=8,
                            popup=f"Drone {drone_id}<br>Battery: {latest_point.get('battery_level', 'N/A')}%<br>Signal: {latest_point.get('signal_strength', 'N/A')}%",
                            color=color,
                            fill=True,
                            fillColor=color
                        ).add_to(m)
            
            # Add discoveries
            if discoveries:
                for discovery in discoveries:
                    discovery_color = 'red' if discovery.get('discovery_type') == 'person' else 'orange'
                    discovery_icon = 'user' if discovery.get('discovery_type') == 'person' else 'exclamation-triangle'
                    
                    folium.Marker(
                        [discovery['position']['lat'], discovery['position']['lng']],
                        popup=f"Discovery: {discovery.get('discovery_type', 'Unknown')}<br>Confidence: {discovery.get('confidence', 0):.2f}<br>Priority: {discovery.get('priority', 'Unknown')}",
                        icon=folium.Icon(color=discovery_color, icon=discovery_icon)
                    ).add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Convert to HTML string
            map_html = m._repr_html_()
            return map_html
            
        except Exception as e:
            logger.error(f"Failed to create mission map: {e}")
            return f"<p>Error creating map: {str(e)}</p>"
    
    def create_realtime_dashboard(self, 
                                 mission_data: Dict[str, Any],
                                 telemetry_data: List[Dict[str, Any]],
                                 discoveries: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create Plotly real-time dashboard"""
        
        try:
            dashboard_data = {}
            
            # Create map visualization
            map_fig = self._create_plotly_map(mission_data, telemetry_data, discoveries)
            dashboard_data['map'] = map_fig.to_html(include_plotlyjs='cdn', div_id="mission-map")
            
            # Create telemetry charts
            if telemetry_data:
                battery_chart = self._create_battery_chart(telemetry_data)
                signal_chart = self._create_signal_chart(telemetry_data)
                
                dashboard_data['battery_chart'] = battery_chart.to_html(include_plotlyjs=False, div_id="battery-chart")
                dashboard_data['signal_chart'] = signal_chart.to_html(include_plotlyjs=False, div_id="signal-chart")
            
            # Create discovery summary
            if discoveries:
                discovery_chart = self._create_discovery_chart(discoveries)
                dashboard_data['discovery_chart'] = discovery_chart.to_html(include_plotlyjs=False, div_id="discovery-chart")
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to create real-time dashboard: {e}")
            return {"error": str(e)}
    
    def _group_telemetry_by_drone(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group telemetry data by drone ID"""
        drone_groups = {}
        
        for telemetry in telemetry_data:
            drone_id = telemetry.get('drone_id', 'unknown')
            if drone_id not in drone_groups:
                drone_groups[drone_id] = []
            
            drone_groups[drone_id].append(telemetry)
        
        return drone_groups
    
    def _create_plotly_map(self, 
                          mission_data: Dict[str, Any],
                          telemetry_data: List[Dict[str, Any]],
                          discoveries: List[Dict[str, Any]] = None) -> go.Figure:
        """Create Plotly map visualization"""
        
        fig = go.Figure()
        
        # Add mission center
        if mission_data.get('center_lat') and mission_data.get('center_lng'):
            fig.add_trace(go.Scattermapbox(
                lat=[mission_data['center_lat']],
                lon=[mission_data['center_lng']],
                mode='markers',
                marker=dict(size=15, color='blue', symbol='home'),
                text=["Mission Center"],
                name="Mission Center",
                showlegend=True
            ))
        
        # Add drone tracks
        if telemetry_data:
            drone_tracks = self._group_telemetry_by_drone(telemetry_data)
            colors = ['red', 'green', 'orange', 'purple', 'darkred']
            
            for i, (drone_id, track_data) in enumerate(drone_tracks.items()):
                color = colors[i % len(colors)]
                
                lats = [point['lat'] for point in track_data]
                lons = [point['lng'] for point in track_data]
                
                # Add track line
                fig.add_trace(go.Scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode='lines',
                    line=dict(color=color, width=3),
                    name=f"Drone {drone_id}",
                    showlegend=True
                ))
                
                # Add current position
                if track_data:
                    latest_point = track_data[-1]
                    fig.add_trace(go.Scattermapbox(
                        lat=[latest_point['lat']],
                        lon=[latest_point['lng']],
                        mode='markers',
                        marker=dict(size=12, color=color, symbol='circle'),
                        text=[f"Drone {drone_id}<br>Battery: {latest_point.get('battery_level', 'N/A')}%"],
                        name=f"Drone {drone_id} Current",
                        showlegend=False
                    ))
        
        # Add discoveries
        if discoveries:
            discovery_lats = [d['position']['lat'] for d in discoveries]
            discovery_lons = [d['position']['lng'] for d in discoveries]
            discovery_types = [d.get('discovery_type', 'Unknown') for d in discoveries]
            discovery_confidences = [d.get('confidence', 0) for d in discoveries]
            
            fig.add_trace(go.Scattermapbox(
                lat=discovery_lats,
                lon=discovery_lons,
                mode='markers',
                marker=dict(
                    size=15,
                    color=discovery_confidences,
                    colorscale='RdYlGn',
                    colorbar=dict(title="Confidence"),
                    symbol='triangle-up'
                ),
                text=[f"{t}<br>Confidence: {c:.2f}" for t, c in zip(discovery_types, discovery_confidences)],
                name="Discoveries",
                showlegend=True
            ))
        
        # Update layout
        fig.update_layout(
            title="SAR Mission Real-time Map",
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=self.default_center[0], lon=self.default_center[1]),
                zoom=self.default_zoom
            ),
            height=600,
            showlegend=True
        )
        
        return fig
    
    def _create_battery_chart(self, telemetry_data: List[Dict[str, Any]]) -> go.Figure:
        """Create battery level chart"""
        
        df = pd.DataFrame(telemetry_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig = go.Figure()
        
        # Group by drone
        for drone_id in df['drone_id'].unique():
            drone_data = df[df['drone_id'] == drone_id]
            
            fig.add_trace(go.Scatter(
                x=drone_data['timestamp'],
                y=drone_data['battery_level'],
                mode='lines+markers',
                name=f"Drone {drone_id}",
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="Drone Battery Levels Over Time",
            xaxis_title="Time",
            yaxis_title="Battery Level (%)",
            height=300
        )
        
        return fig
    
    def _create_signal_chart(self, telemetry_data: List[Dict[str, Any]]) -> go.Figure:
        """Create signal strength chart"""
        
        df = pd.DataFrame(telemetry_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig = go.Figure()
        
        # Group by drone
        for drone_id in df['drone_id'].unique():
            drone_data = df[df['drone_id'] == drone_id]
            
            fig.add_trace(go.Scatter(
                x=drone_data['timestamp'],
                y=drone_data['signal_strength'],
                mode='lines+markers',
                name=f"Drone {drone_id}",
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="Drone Signal Strength Over Time",
            xaxis_title="Time",
            yaxis_title="Signal Strength (%)",
            height=300
        )
        
        return fig
    
    def _create_discovery_chart(self, discoveries: List[Dict[str, Any]]) -> go.Figure:
        """Create discovery summary chart"""
        
        discovery_types = [d.get('discovery_type', 'Unknown') for d in discoveries]
        type_counts = pd.Series(discovery_types).value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            hole=0.3
        )])
        
        fig.update_layout(
            title="Discovery Types Summary",
            height=300
        )
        
        return fig
    
    def calculate_search_coverage(self, 
                                 search_area: List[Dict[str, float]],
                                 drone_tracks: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Calculate search coverage metrics"""
        
        try:
            # Calculate total search area
            total_area = self._calculate_polygon_area(search_area)
            
            # Calculate covered area by drone tracks
            covered_area = 0
            for drone_id, track in drone_tracks.items():
                drone_covered = self._calculate_track_coverage(track)
                covered_area += drone_covered
            
            # Calculate coverage percentage
            coverage_percentage = (covered_area / total_area * 100) if total_area > 0 else 0
            
            return {
                "total_area_km2": total_area,
                "covered_area_km2": covered_area,
                "coverage_percentage": coverage_percentage,
                "remaining_area_km2": total_area - covered_area,
                "efficiency_score": min(coverage_percentage, 100)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate search coverage: {e}")
            return {"error": str(e)}
    
    def _calculate_polygon_area(self, coordinates: List[Dict[str, float]]) -> float:
        """Calculate polygon area using shoelace formula"""
        
        if len(coordinates) < 3:
            return 0.0
        
        # Convert to numpy array
        coords = np.array([[coord['lat'], coord['lng']] for coord in coordinates])
        
        # Shoelace formula
        x = coords[:, 1]  # longitude
        y = coords[:, 0]  # latitude
        
        area = 0.5 * abs(sum(x[i] * y[i + 1] - x[i + 1] * y[i] for i in range(-1, len(x) - 1)))
        
        # Convert to km² (rough approximation)
        area_km2 = area * (111 * 111)  # 1 degree ≈ 111 km
        
        return area_km2
    
    def _calculate_track_coverage(self, track: List[Dict[str, Any]]) -> float:
        """Calculate area covered by drone track"""
        
        if len(track) < 2:
            return 0.0
        
        # Assume drone has a search swath width of 100m
        swath_width = 0.1  # km
        
        total_distance = 0
        for i in range(len(track) - 1):
            point1 = track[i]
            point2 = track[i + 1]
            
            distance = self._calculate_distance(
                point1['lat'], point1['lng'],
                point2['lat'], point2['lng']
            )
            total_distance += distance
        
        # Calculate covered area
        covered_area = total_distance * swath_width / 1000  # Convert to km²
        
        return covered_area
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in km"""
        
        R = 6371  # Earth's radius in km
        
        lat1_rad = np.radians(lat1)
        lng1_rad = np.radians(lng1)
        lat2_rad = np.radians(lat2)
        lng2_rad = np.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlng/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def export_mission_data(self, 
                           mission_data: Dict[str, Any],
                           telemetry_data: List[Dict[str, Any]],
                           discoveries: List[Dict[str, Any]] = None,
                           format: str = "geojson") -> str:
        """Export mission data in various formats"""
        
        try:
            if format == "geojson":
                return self._export_as_geojson(mission_data, telemetry_data, discoveries)
            elif format == "csv":
                return self._export_as_csv(telemetry_data, discoveries)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export mission data: {e}")
            return json.dumps({"error": str(e)})
    
    def _export_as_geojson(self, 
                          mission_data: Dict[str, Any],
                          telemetry_data: List[Dict[str, Any]],
                          discoveries: List[Dict[str, Any]] = None) -> str:
        """Export mission data as GeoJSON"""
        
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        # Add mission center
        if mission_data.get('center_lat') and mission_data.get('center_lng'):
            geojson["features"].append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [mission_data['center_lng'], mission_data['center_lat']]
                },
                "properties": {
                    "type": "mission_center",
                    "name": mission_data.get('name', 'Unknown'),
                    "description": f"Mission center for {mission_data.get('name', 'Unknown')}"
                }
            })
        
        # Add drone tracks
        drone_tracks = self._group_telemetry_by_drone(telemetry_data)
        for drone_id, track in drone_tracks.items():
            coordinates = [[point['lng'], point['lat']] for point in track]
            
            geojson["features"].append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                },
                "properties": {
                    "type": "drone_track",
                    "drone_id": drone_id,
                    "description": f"Flight track for drone {drone_id}"
                }
            })
        
        # Add discoveries
        if discoveries:
            for discovery in discoveries:
                geojson["features"].append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [discovery['position']['lng'], discovery['position']['lat']]
                    },
                    "properties": {
                        "type": "discovery",
                        "discovery_type": discovery.get('discovery_type', 'Unknown'),
                        "confidence": discovery.get('confidence', 0),
                        "priority": discovery.get('priority', 'Unknown'),
                        "description": f"Discovery of {discovery.get('discovery_type', 'Unknown')}"
                    }
                })
        
        return json.dumps(geojson, indent=2)
    
    def _export_as_csv(self, 
                      telemetry_data: List[Dict[str, Any]],
                      discoveries: List[Dict[str, Any]] = None) -> str:
        """Export mission data as CSV"""
        
        # Export telemetry data
        telemetry_df = pd.DataFrame(telemetry_data)
        telemetry_csv = telemetry_df.to_csv(index=False)
        
        # Export discoveries data
        discoveries_csv = ""
        if discoveries:
            discoveries_df = pd.DataFrame(discoveries)
            discoveries_csv = discoveries_df.to_csv(index=False)
        
        return f"=== TELEMETRY DATA ===\n{telemetry_csv}\n\n=== DISCOVERIES DATA ===\n{discoveries_csv}"

# Global mapping utilities instance
mapping_utils = SARMappingUtils()
