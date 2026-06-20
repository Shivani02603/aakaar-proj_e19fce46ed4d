'use client';  

import { useState } from 'react';  
import { useRouter } from 'next/navigation';  
import { createSession } from '@/lib/api';  

interface SessionCreateRequest {  
  name: string;  
}  

export default function NewSessionPage() {  
  const [name, setName] = useState<string>('');  
  const [loading, setLoading] = useState<boolean>(false);  
  const [error, setError] = useState<string | null>(null);  
  const router = useRouter();  

  const handleSubmit = async (e: React.FormEvent) => {  
    e.preventDefault();  
    setLoading(true);  
    setError(null);  

    if (!name.trim()) {  
      setError('Name is required.');  
      setLoading(false);  
      return;  
    }  

    try {  
      const payload: SessionCreateRequest = { name };  
      await createSession(payload);  
      router.push('/sessions');  
    } catch (err) {  
      setError('Failed to create session. Please try again later.');  
    } finally {  
      setLoading(false);  
    }  
  };  

  return (  
    <div className="container mx-auto px-4 py-8">  
      <h1 className="text-2xl font-bold mb-4">Create New Session</h1>  
      <form onSubmit={handleSubmit} className="max-w-md mx-auto">  
        <div className="mb-4">  
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">  
            Name  
          </label>  
          <input  
            id="name"  
            type="text"  
            value={name}  
            onChange={(e) => setName(e.target.value)}  
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"  
          />  
        </div>  
        {error && <div className="text-red-500 mb-4">{error}</div>}  
        <button  
          type="submit"  
          disabled={loading}  
          className={`w-full px-4 py-2 text-white rounded-md ${loading ? 'bg-gray-400' : 'bg-indigo-500 hover:bg-indigo-600'}`}  
        >  
          {loading ? 'Creating...' : 'Create Session'}  
        </button>  
      </form>  
    </div>  
  );  
}