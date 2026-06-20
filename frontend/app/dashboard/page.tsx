```tsx
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface StatCardProps {
  title: string;
  count: number;
  link: string;
}

const StatCard = ({ title, count, link }: StatCardProps) => (
  <div className="bg-white shadow-md rounded-lg p-6 flex flex-col items-center">
    <h3 className="text-lg font-semibold text-gray-700">{title}</h3>
    <p className="text-2xl font-bold text-blue-600">{count}</p>
    <Link href={link}>
      <a className="mt-4 text-blue-500 hover:underline">View Details</a>
    </Link>
  </div>
);

interface RecentItem {
  id: string;
  name: string;
  createdAt: string;
  type: string;
}

const DashboardPage = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{ sessions: number; uploads: number; aiQueries: number }>({
    sessions: 0,
    uploads: 0,
    aiQueries: 0,
  });
  const [recentItems, setRecentItems] = useState<RecentItem[]>([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/dashboard');
        if (!response.ok) {
          throw new Error('Failed to fetch dashboard data');
        }

        const data = await response.json();
        setStats({
          sessions: data.sessionsCount,
          uploads: data.uploadsCount,
          aiQueries: data.aiQueriesCount,
        });
        setRecentItems(data.recentItems);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Dashboard</h1>

      {loading && <p className="text-gray-600">Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <StatCard title="Sessions" count={stats.sessions} link="/sessions" />
            <StatCard title="Uploads" count={stats.uploads} link="/upload" />
            <StatCard title="AI Queries" count={stats.aiQueries} link="/ai" />
          </div>

          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Recent Items</h2>
            <table className="w-full border-collapse border border-gray-200">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-200 px-4 py-2 text-left text-gray-600">Name</th>
                  <th className="border border-gray-200 px-4 py-2 text-left text-gray-600">Type</th>
                  <th className="border border-gray-200 px-4 py-2 text-left text-gray-600">Created At</th>
                  <th className="border border-gray-200 px-4 py-2 text-left text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentItems.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="border border-gray-200 px-4 py-2">{item.name}</td>
                    <td className="border border-gray-200 px-4 py-2">{item.type}</td>
                    <td className="border border-gray-200 px-4 py-2">{new Date(item.createdAt).toLocaleString()}</td>
                    <td className="border border-gray-200 px-4 py-2">
                      <Link href={`/${item.type}/${item.id}`}>
                        <a className="text-blue-500 hover:underline">View</a>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default DashboardPage;
```