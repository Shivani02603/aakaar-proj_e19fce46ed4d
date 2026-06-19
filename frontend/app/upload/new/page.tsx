'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-toastify';
import { createUpload } from '@/lib/api';

interface UploadForm {
  fileName: string;
  fileType: string;
  fileSize: number;
}

export default function NewUploadPage() {
  const [form, setForm] = useState<UploadForm>({
    fileName: '',
    fileType: '',
    fileSize: 0,
  });
  const [loading, setLoading] = useState<boolean>(false);
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: name === 'fileSize' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.fileName || !form.fileType || form.fileSize <= 0) {
      toast.error('Please fill out all fields correctly.');
      return;
    }

    try {
      setLoading(true);
      await createUpload(form);
      toast.success('Upload created successfully.');
      router.push('/upload');
    } catch (err) {
      toast.error('Failed to create upload.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-4">New Upload</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="fileName" className="block text-sm font-medium text-gray-700">
            File Name
          </label>
          <input
            type="text"
            id="fileName"
            name="fileName"
            value={form.fileName}
            onChange={handleChange}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2"
            required
          />
        </div>
        <div>
          <label htmlFor="fileType" className="block text-sm font-medium text-gray-700">
            File Type
          </label>
          <input
            type="text"
            id="fileType"
            name="fileType"
            value={form.fileType}
            onChange={handleChange}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2"
            required
          />
        </div>
        <div>
          <label htmlFor="fileSize" className="block text-sm font-medium text-gray-700">
            File Size (KB)
          </label>
          <input
            type="number"
            id="fileSize"
            name="fileSize"
            value={form.fileSize}
            onChange={handleChange}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2"
            required
          />
        </div>
        <div>
          <button
            type="submit"
            className={`bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            disabled={loading}
          >
            {loading ? 'Submitting...' : 'Submit'}
          </button>
        </div>
      </form>
    </div>
  );
}