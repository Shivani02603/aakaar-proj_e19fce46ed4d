'use client';  

import { useEffect, useState } from 'react';  
import { useRouter } from 'next/navigation';  
import { listSessions, deleteSession } from '@/lib/api';  

interface Session {  
  id: string;  
  name: string;  
  createdAt: string;  
}  

export default function SessionsPage() {  
  const [sessions, setSessions] = useState<Session[]>([]);  
  const [loading, setLoading] = useState<boolean>(true);  
  const [error, setError] = useState<string | null>(null);  
  const router = useRouter();  

  useEffect(() => {  
    const fetchSessions = async () => {  
      setLoading(true);  
      setError(null);  
      try {  
        const response = await listSessions();  
        setSessions(response);  
      } catch (err) {  
        setError('Failed to fetch sessions. Please try again later.');  
      } finally {  
        setLoading(false);  
      }  
    };  

    fetchSessions();  
  }, []);  

  const handleDelete = async (id: string) => {  
    try {  
      await deleteSession(id);  
      setSessions((prev) => prev.filter((session) => session.id !== id));  
    } catch (err) {  
      setError('Failed to delete session. Please try again later.');  
    }  
  };  

  if (loading) {  
    return <div className="text-center py-4">Loading...</div>;  
  }  

  if (error) {  
    return <div className="text-center py-4 text-red-500">{error}</div>;  
  }  

  return (  
    <div className="container mx-auto px-4 py-8">  
      <h1 className="text-2xl font-bold mb-4">Sessions</h1>  
      <table className="table-auto w-full border-collapse border border-gray-300">  
        <thead>  
          <tr className="bg-gray-100">  
            <th className="border border-gray-300 px-4 py-2">ID</th>  
            <th className="border border-gray-300 px-4 py-2">Name</th>  
            <th className="border border-gray-300 px-4 py-2">Created At</th>  
            <th className="border border-gray-300 px-4 py-2">Actions</th>  
          </tr>  
        </thead>  
        <tbody>  
          {sessions.map((session) => (  
            <tr key={session.id}>  
              <td className="border border-gray-300 px-4 py-2">{session.id}</td>  
              <td className="border border-gray-300 px-4 py-2">{session.name}</td>  
              <td className="border border-gray-300 px-4 py-2">{new Date(session.createdAt).toLocaleString()}</td>  
              <td className="border border-gray-300 px-4 py-2">  
                <button  
                  className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"  
                  onClick={() => handleDelete(session.id)}  
                >  
                  Delete  
                </button>  
              </td>  
            </tr>  
          ))}  
        </tbody>  
      </table>  
    </div>  
  );  
}