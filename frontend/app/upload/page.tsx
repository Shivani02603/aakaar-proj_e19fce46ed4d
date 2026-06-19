'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-toastify';
import { getUploads, deleteUpload } from '@/lib/api';

interface Upload {
  id: string;
  fileName: string;
  fileType: string;
  fileSize: number;
  createdAt: string;
}

export default function UploadPage() {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchUploads = async () => {
      try {
        setLoading(true);
        const response = await getUploads();
        setUploads(response);
      } catch (err) {
        setError('Failed to fetch uploads.');
      } finally {
        setLoading(false);
      }
    };

    fetchUploads();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteUpload(id);
      setUploads((prev) => prev.filter((upload) => upload.id !== id));
      toast.success('Upload deleted successfully.');
    } catch (err) {
      toast.error('Failed to delete upload.');
    }
  };

  if (loading) {
    return <div className="text-center mt-10">Loading...</div>;
  }

  if (error) {
    return <div className="text-center mt-10 text-red-500">{error}</div>;
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-4">Uploads</h1>
      <table className="table-auto w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border border-gray-300 px-4 py-2">File Name</th>
            <th className="border border-gray-300 px-4 py-2">File Type</th>
            <th className="border border-gray-300 px-4 py-2">File Size</th>
            <th className="border border-gray-300 px-4 py-2">Uploaded At</th>
            <th className="border border-gray-300 px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {uploads.map((upload) => (
            <tr key={upload.id}>
              <td className="border border-gray-300 px-4 py-2">{upload.fileName}</td>
              <td className="border border-gray-300 px-4 py-2">{upload.fileType}</td>
              <td className="border border-gray-300 px-4 py-2">{upload.fileSize} KB</td>
              <td className="border border-gray-300 px-4 py-2">{new Date(upload.createdAt).toLocaleString()}</td>
              <td className="border border-gray-300 px-4 py-2">
                <button
                  className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                  onClick={() => handleDelete(upload.id)}
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