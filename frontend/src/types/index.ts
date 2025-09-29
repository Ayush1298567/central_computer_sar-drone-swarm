/**
 * Main types index file - exports all TypeScript types.
 */

export * from './api';

// Additional types can be added here
export interface Position {
  lat: number;
  lng: number;
  altitude?: number;
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface WeatherData {
  temperature: number;
  wind_speed: number;
  wind_direction: number;
  visibility: number;
  conditions: string;
  humidity: number;
  pressure: number;
}

export interface FlightPlan {
  waypoints: Position[];
  altitude: number;
  speed: number;
  pattern: 'lawnmower' | 'spiral' | 'grid' | 'adaptive';
}

export interface MissionPlan {
  mission: Mission;
  drones: Drone[];
  flight_plans: Record<number, FlightPlan>;
  estimated_duration: number;
  coverage_area: number;
  safety_constraints: any;
}