import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Activity,
  Map,
  MessageSquare,
  Settings,
  Bell,
  Menu,
  X,
  Plane,
  Search,
  BarChart3
} from 'lucide-react';
import { cn } from '../../utils/cn';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    {
      name: 'Dashboard',
      href: '/',
      icon: Activity,
      current: location.pathname === '/'
    },
    {
      name: 'Mission Planning',
      href: '/mission-planning',
      icon: Map,
      current: location.pathname === '/mission-planning'
    },
    {
      name: 'Live Mission',
      href: '/live-mission',
      icon: Plane,
      current: location.pathname.startsWith('/live-mission')
    },
    {
      name: 'Drones',
      href: '/drones',
      icon: Plane,
      current: location.pathname === '/drones'
    },
    {
      name: 'Discoveries',
      href: '/discoveries',
      icon: Search,
      current: location.pathname === '/discoveries'
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: BarChart3,
      current: location.pathname === '/analytics'
    },
    {
      name: 'Chat',
      href: '/chat',
      icon: MessageSquare,
      current: location.pathname === '/chat'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
      current: location.pathname === '/settings'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-16 items-center justify-between px-4 border-b border-gray-200">
          <div className="flex items-center">
            <Plane className="h-8 w-8 text-primary-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">
              SAR Commander
            </span>
          </div>
          <button
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-8 px-4">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={cn(
                      "group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors",
                      item.current
                        ? "bg-primary-100 text-primary-900"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    )}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className={cn(
                      "mr-3 h-5 w-5 flex-shrink-0",
                      item.current ? "text-primary-500" : "text-gray-400 group-hover:text-gray-500"
                    )} />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Status indicators */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">System Status</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Backend API</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                  <span className="text-xs text-gray-600">Online</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">WebSocket</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                  <span className="text-xs text-gray-600">Connected</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Active Drones</span>
                <span className="text-xs text-gray-600">3/5</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 shadow-sm">
          <button
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex items-center space-x-4">
            <div className="hidden md:block">
              <h1 className="text-lg font-semibold text-gray-900">
                {navigation.find(item => item.current)?.name || 'SAR Mission Commander'}
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <button className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 relative">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 block h-2 w-2 rounded-full bg-red-400 ring-2 ring-white"></span>
            </button>

            {/* User menu */}
            <div className="flex items-center">
              <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center">
                <span className="text-sm font-medium text-white">JD</span>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1">
          <div className="py-6">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;