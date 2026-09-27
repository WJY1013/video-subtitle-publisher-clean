import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export default function Home() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['douyin', 'xhs']);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [videos, setVideos] = useState<any[]>([]);

  const platforms = ['douyin', 'xhs', 'bilibili', 'kuaishou', 'wevideo', 'weibo'];
  const platformNames: { [key: string]: string } = {
    douyin: '抖音',
    xhs: '小红书',
    bilibili: 'B站',
    kuaishou: '快手',
    wevideo: 'WeVideo',
    weibo: '微博'
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setVideoFile(e.target.files[0]);
    }
  };

  const togglePlatform = (platform: string) => {
    setSelectedPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  const handleUpload = async () => {
    if (!videoFile || !title) {
      alert('Please select a video file and enter a title');
      return;
    }

    setLoading(true);
    setUploadStatus('Uploading...');

    const formData = new FormData();
    formData.append('file', videoFile);
    formData.append('title', title);
    formData.append('description', description);

    try {
      const response = await axios.post(`${API_URL}/api/v1/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setUploadStatus('✅ Upload successful!');
      setVideoFile(null);
      setTitle('');
      setDescription('');
      fetchVideos();
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStatus('❌ Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const fetchVideos = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/videos`);
      setVideos(response.data.videos);
    } catch (error) {
      console.error('Failed to fetch videos:', error);
    }
  };

  const handlePublish = async (videoId: string) => {
    const platformString = selectedPlatforms.join(',');
    try {
      setUploadStatus(`Publishing to ${selectedPlatforms.length} platforms...`);
      const response = await axios.post(`${API_URL}/api/v1/publish`, {
        video_id: videoId,
        platforms: platformString
      }, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      setUploadStatus(`✅ Published to ${selectedPlatforms.length} platforms!`);
    } catch (error) {
      console.error('Publish failed:', error);
      setUploadStatus('❌ Publish failed');
    }
  };

  React.useEffect(() => {
    fetchVideos();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-800 mb-2">🌊 GULF</h1>
          <p className="text-xl text-gray-600">Video Subtitle Publisher</p>
          <p className="text-sm text-gray-500 mt-2">Multi-platform video publishing made simple</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">📤 Upload Video</h2>

            {/* File Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Video File</label>
              <input
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                className="w-full px-4 py-3 border-2 border-dashed border-indigo-300 rounded-lg focus:outline-none"
              />
              {videoFile && <p className="text-sm text-green-600 mt-2">✓ {videoFile.name}</p>}
            </div>

            {/* Title Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Video Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter video title"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {/* Description Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter video description"
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {/* Platform Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">Select Platforms</label>
              <div className="grid grid-cols-2 gap-3">
                {platforms.map((platform) => (
                  <button
                    key={platform}
                    onClick={() => togglePlatform(platform)}
                    className={`px-4 py-2 rounded-lg font-medium transition ${
                      selectedPlatforms.includes(platform)
                        ? 'bg-indigo-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {platformNames[platform]}
                  </button>
                ))}
              </div>
            </div>

            {/* Status Message */}
            {uploadStatus && (
              <div className={`mb-6 p-3 rounded-lg text-sm ${
                uploadStatus.includes('✅')
                  ? 'bg-green-100 text-green-800'
                  : uploadStatus.includes('❌')
                  ? 'bg-red-100 text-red-800'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {uploadStatus}
              </div>
            )}

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-3 rounded-lg font-bold hover:bg-indigo-700 disabled:bg-gray-400 transition"
            >
              {loading ? '⏳ Uploading...' : '🚀 Upload & Generate Subtitles'}
            </button>
          </div>

          {/* Videos List Section */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">📹 Your Videos</h2>

            {videos.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <p>No videos yet</p>
                <p className="text-sm">Upload your first video to get started</p>
              </div>
            ) : (
              <div className="space-y-4">
                {videos.map((video) => (
                  <div
                    key={video.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
                  >
                    <h3 className="font-bold text-gray-800 mb-2">{video.title}</h3>
                    <p className="text-sm text-gray-600 mb-3">{video.description}</p>

                    <div className="flex items-center justify-between mb-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        video.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {video.status}
                      </span>
                      <span className="text-xs text-gray-500">{video.id}</span>
                    </div>

                    <button
                      onClick={() => handlePublish(video.id)}
                      className="w-full bg-green-600 text-white py-2 rounded-lg font-medium hover:bg-green-700 transition text-sm"
                    >
                      Publish to {selectedPlatforms.length} Platform{selectedPlatforms.length !== 1 ? 's' : ''}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl mb-3">⚡</div>
            <h3 className="font-bold text-gray-800 mb-2">Fast Upload</h3>
            <p className="text-gray-600 text-sm">Quick and reliable video upload with progress tracking</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl mb-3">🎯</div>
            <h3 className="font-bold text-gray-800 mb-2">Auto Subtitles</h3>
            <p className="text-gray-600 text-sm">Automatic subtitle generation in multiple languages</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl mb-3">🌍</div>
            <h3 className="font-bold text-gray-800 mb-2">Multi-Platform</h3>
            <p className="text-gray-600 text-sm">Publish to all major platforms with one click</p>
          </div>
        </div>
      </div>
    </div>
  );
}
