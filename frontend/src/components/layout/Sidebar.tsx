import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MapPin, 
  Radio, 
  Search, 
  Settings,
  FileText,
  AlertTriangle,
  Activity
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const navItems = [
    {
      to: '/dashboard',
      icon: LayoutDashboard,
      label: 'Dashboard',
      description: 'Mission overview'
    },
    {
      to: '/mission-planning',
      icon: MapPin,
      label: 'Mission Planning',
      description: 'Plan new missions'
    },
    {
      to: '/live-missions',
      icon: Radio,
      label: 'Live Missions',
      description: 'Active operations'
    },
    {
      to: '/drone-fleet',
      icon: Activity,
      label: 'Drone Fleet',
      description: 'Fleet management'
    },
    {
      to: '/discoveries',
      icon: Search,
      label: 'Discoveries',
      description: 'Search results'
    },
    {
      to: '/reports',
      icon: FileText,
      label: 'Reports',
      description: 'Mission reports'
    },
    {
      to: '/alerts',
      icon: AlertTriangle,
      label: 'Alerts',
      description: 'System alerts'
    },
    {
      to: '/settings',
      icon: Settings,
      label: 'Settings',
      description: 'System configuration'
    }
  ];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 h-[calc(100vh-73px)]">
      <nav className="p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const IconComponent = item.icon;
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 p-3 rounded-lg transition-colors group ${
                      isActive
                        ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`
                  }
                >
                  <IconComponent className="w-5 h-5" />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{item.label}</div>
                    <div className="text-xs text-gray-500 group-hover:text-gray-600">
                      {item.description}
                    </div>
                  </div>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* System Status */}
      <div className="absolute bottom-4 left-4 right-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">System Status</span>
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          </div>
          <div className="space-y-1 text-xs text-gray-600">
            <div className="flex justify-between">
              <span>API</span>
              <span className="text-green-600">Online</span>
            </div>
            <div className="flex justify-between">
              <span>Drones</span>
              <span className="text-green-600">3 Connected</span>
            </div>
            <div className="flex justify-between">
              <span>Missions</span>
              <span className="text-blue-600">2 Active</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;