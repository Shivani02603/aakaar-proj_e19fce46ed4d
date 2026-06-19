```tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/lib/auth';
import { toast } from 'react-toastify';

interface StatCardProps {
  title: string;
  count: number;
  description: string;
}

interface RecentItem {
  id: string;
  name: string;
  type: string;
  createdAt: string;
}

const StatCard = ({ title, count, description }: StatCardProps) => (
  <div className="bg-white shadow-md rounded-lg p-4">
    <h3 className="text-lg font-semibold">{title}</h3>
    <p className="text-2xl font-bold mt-2">{count}</p>
    <p className="text-sm text-gray-500 mt-1">{description}</p>
  </div>
);

const DashboardPage = () => {
  const [sessionsCount, setSessionsCount] = useState<number>(0);
  const [uploadsCount, setUploadsCount] = useState<number>(0);
  const [aiQueriesCount, setAiQueriesCount] = useState<number>(0);
  const [recentItems, setRecentItems] = useState<RecentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      const token = getToken();
      if (!token) {
        router.push('/login');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const sessionsResponse = await fetch('/api/sessions', {
          headers: { Authorization: `Bearer ${token}` },
        });
        const uploadsResponse = await fetch('/api/upload', {
          headers: { Authorization: `Bearer ${token}` },
        });
        const aiQueriesResponse = await fetch('/api/ai/query', {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!sessionsResponse.ok || !uploadsResponse.ok || !aiQueriesResponse.ok) {
          throw new Error('Failed to fetch data');
        }

        const sessionsData = await sessionsResponse.json();
        const uploadsData = await uploadsResponse.json();
        const aiQueriesData = await aiQueriesResponse.json();

        setSessionsCount(sessionsData.length);
        setUploadsCount(uploadsData.length);
        setAiQueriesCount(aiQueriesData.length);

        const recentItemsData: RecentItem[] = [
          ...sessionsData.map((item: any) => ({
            id: item.id,
            name: item.title,
            type: 'Session',
            createdAt: item.createdAt,
          })),
          ...uploadsData.map((item: any) => ({
            id: item.id,
            name: item.filename,
            type: 'Upload',
            createdAt: item.createdAt,
          })),
          ...aiQueriesData.map((item: any) => ({
            id: item.id,
            name: item.query,
            type: 'AI Query',
            createdAt: item.createdAt,
          })),
        ].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

        setRecentItems(recentItemsData.slice(0, 5));
      } catch (err) {
        setError('Failed to load dashboard data.');
        toast.error('Error loading dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  if (loading) {
    return <p className="text-center mt-4">Loading...</p>;
  }

  if (error) {
    return <p className="text-center mt-4 text-red-500">{error}</p>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <StatCard title="Sessions" count={sessionsCount} description="Total sessions created" />
        <StatCard title="Uploads" count={uploadsCount} description="Total files uploaded" />
        <StatCard title="AI Queries" count={aiQueriesCount} description="Total AI queries made" />
      </div>
      <div className="bg-white shadow-md rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4">Recent Items</h2>
        <table className="w-full border-collapse border border-gray-200">
          <thead>
            <tr className="bg-gray-100">
              <th className="border border-gray-200 px-4 py-2 text-left">Name</th>
              <th className="border border-gray-200 px-4 py-2 text-left">Type</th>
              <th className="border border-gray-200 px-4 py-2 text-left">Created At</th>
            </tr>
          </thead>
          <tbody>
            {recentItems.map((item) => (
              <tr key={item.id}>
                <td className="border border-gray-200 px-4 py-2">{item.name}</td>
                <td className="border border-gray-200 px-4 py-2">{item.type}</td>
                <td className="border border-gray-200 px-4 py-2">{new Date(item.createdAt).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DashboardPage;
```