'use client';

import Link from 'next/link';
import { useAuth } from '../providers/AuthProvider';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4 py-2 flex justify-between items-center">
        <Link href="/dashboard" className="text-lg font-bold text-blue-600">
          Aakaar Project
        </Link>
        <div className="flex items-center space-x-4">
          {user ? (
            <>
              <Link href="/sessions" className="text-gray-700 hover:text-blue-600">
                Sessions
              </Link>
              <Link href="/upload" className="text-gray-700 hover:text-blue-600">
                Upload
              </Link>
              <button
                onClick={logout}
                className="text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-gray-700 hover:text-blue-600">
                Login
              </Link>
              <Link href="/register" className="text-gray-700 hover:text-blue-600">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}