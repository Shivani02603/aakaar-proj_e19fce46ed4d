'use client';

import { useAuth } from '../providers/AuthProvider';
import { removeToken } from '../lib/auth';
import { useRouter } from 'next/navigation';

export default function Navbar() {
  const { user, setUser } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    removeToken();
    setUser(null);
    router.push('/login');
  };

  return (
    <nav className="bg-blue-600 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <div className="text-lg font-bold">Aakaar Project</div>
        <div className="flex items-center space-x-4">
          {user ? (
            <>
              <span>Welcome, {user.name}</span>
              <button
                onClick={handleLogout}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => router.push('/login')}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
              >
                Login
              </button>
              <button
                onClick={() => router.push('/register')}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
              >
                Register
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}