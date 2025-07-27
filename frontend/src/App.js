import React, { useState, useRef } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [uploadedData, setUploadedData] = useState(null);
  const [calculations, setCalculations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [days, setDays] = useState(30);
  const [productFilter, setProductFilter] = useState('');
  const [packagingFilter, setPackagingFilter] = useState('');
  const [geminiQuery, setGeminiQuery] = useState('');
  const [geminiResponse, setGeminiResponse] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const fileInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-excel`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setUploadedData(data);
      setActiveTab('calculate');
    } catch (err) {
      setError(`Upload failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCalculate = async () => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/calculate/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          days: parseInt(days),
          product_filter: productFilter || null,
          packaging_filter: packagingFilter || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setCalculations(data);
      setActiveTab('results');
    } catch (err) {
      setError(`Calculation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGeminiQuery = async () => {
    if (!sessionId || !geminiQuery.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/gemini-query/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: geminiQuery,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setGeminiResponse(data);
    } catch (err) {
      setError(`Gemini query failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetApp = () => {
    setSessionId(null);
    setUploadedData(null);
    setCalculations(null);
    setGeminiResponse(null);
    setError(null);
    setActiveTab('upload');
    setDays(30);
    setProductFilter('');
    setPackagingFilter('');
    setGeminiQuery('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg">
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Stock Management System
            </h1>
            <p className="text-gray-600">
              Upload Excel files to analyze stock levels and calculate depot requirements
            </p>
          </div>

          <div className="p-6">
            {/* Tab Navigation */}
            <div className="flex space-x-4 mb-6">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-lg font-medium ${
                  activeTab === 'upload'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Upload Data
              </button>
              <button
                onClick={() => setActiveTab('calculate')}
                className={`px-4 py-2 rounded-lg font-medium ${
                  activeTab === 'calculate'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                } ${!sessionId ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={!sessionId}
              >
                Calculate Requirements
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className={`px-4 py-2 rounded-lg font-medium ${
                  activeTab === 'results'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                } ${!calculations ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={!calculations}
              >
                View Results
              </button>
              <button
                onClick={() => setActiveTab('ai')}
                className={`px-4 py-2 rounded-lg font-medium ${
                  activeTab === 'ai'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                } ${!sessionId ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={!sessionId}
              >
                AI Insights
              </button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                {error}
              </div>
            )}

            {/* Upload Tab */}
            {activeTab === 'upload' && (
              <div className="space-y-6">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer flex flex-col items-center space-y-2"
                  >
                    <div className="text-4xl text-gray-400">📊</div>
                    <div className="text-lg font-medium text-gray-700">
                      Upload Excel File
                    </div>
                    <div className="text-sm text-gray-500">
                      Choose a .xlsx or .xls file with stock and order data
                    </div>
                  </label>
                </div>

                {uploadedData && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h3 className="font-medium text-green-800 mb-2">Upload Successful!</h3>
                    <div className="text-sm text-green-700 space-y-1">
                      <p>Records processed: {uploadedData.records_count}</p>
                      <p>Date range: {uploadedData.date_range.start} to {uploadedData.date_range.end}</p>
                      <p>Total days: {uploadedData.date_range.total_days}</p>
                      <p>Depots: {uploadedData.depots.length}</p>
                      <p>Products: {uploadedData.products.length}</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Calculate Tab */}
            {activeTab === 'calculate' && uploadedData && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Days to Cover
                    </label>
                    <input
                      type="number"
                      value={days}
                      onChange={(e) => setDays(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-lg"
                      min="1"
                      max="365"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Product Filter
                    </label>
                    <input
                      type="text"
                      value={productFilter}
                      onChange={(e) => setProductFilter(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-lg"
                      placeholder="e.g., COCA-COLA"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Packaging Filter
                    </label>
                    <select
                      value={packagingFilter}
                      onChange={(e) => setPackagingFilter(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-lg"
                    >
                      <option value="">All Packaging Types</option>
                      <option value="Verre">Verre</option>
                      <option value="Pet">Pet</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={handleCalculate}
                  disabled={loading}
                  className="w-full bg-blue-500 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50"
                >
                  {loading ? 'Calculating...' : 'Calculate Requirements'}
                </button>
              </div>
            )}

            {/* Results Tab */}
            {activeTab === 'results' && calculations && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {calculations.summary.total_depots}
                    </div>
                    <div className="text-sm text-blue-700">Total Depots</div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {calculations.summary.total_products}
                    </div>
                    <div className="text-sm text-green-700">Total Products</div>
                  </div>
                  <div className="bg-yellow-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600">
                      {calculations.summary.high_priority.length}
                    </div>
                    <div className="text-sm text-yellow-700">High Priority (&lt;7 days)</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-gray-600">
                      {calculations.summary.no_stock_needed.length}
                    </div>
                    <div className="text-sm text-gray-700">No Stock Needed</div>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border border-gray-300">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="border border-gray-300 p-2 text-left">Depot</th>
                        <th className="border border-gray-300 p-2 text-left">Product</th>
                        <th className="border border-gray-300 p-2 text-left">Packaging</th>
                        <th className="border border-gray-300 p-2 text-right">ADC</th>
                        <th className="border border-gray-300 p-2 text-right">DOC</th>
                        <th className="border border-gray-300 p-2 text-right">Current Stock</th>
                        <th className="border border-gray-300 p-2 text-right">Quantity to Send</th>
                      </tr>
                    </thead>
                    <tbody>
                      {calculations.calculations.map((item, index) => (
                        <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="border border-gray-300 p-2">{item.depot}</td>
                          <td className="border border-gray-300 p-2">{item.article_name}</td>
                          <td className="border border-gray-300 p-2">{item.packaging_type}</td>
                          <td className="border border-gray-300 p-2 text-right">{item.average_daily_consumption}</td>
                          <td className="border border-gray-300 p-2 text-right">
                            <span className={item.days_of_coverage !== 'Infinite' && item.days_of_coverage < 7 ? 'text-red-600 font-bold' : ''}>
                              {item.days_of_coverage}
                            </span>
                          </td>
                          <td className="border border-gray-300 p-2 text-right">{item.current_stock}</td>
                          <td className="border border-gray-300 p-2 text-right">
                            <span className={item.quantity_to_send > 0 ? 'text-blue-600 font-bold' : 'text-gray-500'}>
                              {item.quantity_to_send}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* AI Insights Tab */}
            {activeTab === 'ai' && sessionId && (
              <div className="space-y-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-medium text-blue-800 mb-2">AI-Powered Insights</h3>
                  <p className="text-sm text-blue-700">
                    Ask questions about your data, get consumption insights, or identify anomalies.
                  </p>
                </div>

                <div className="flex space-x-4">
                  <input
                    type="text"
                    value={geminiQuery}
                    onChange={(e) => setGeminiQuery(e.target.value)}
                    className="flex-1 p-2 border border-gray-300 rounded-lg"
                    placeholder="e.g., Which depots will run out in less than 7 days?"
                  />
                  <button
                    onClick={handleGeminiQuery}
                    disabled={loading || !geminiQuery.trim()}
                    className="bg-green-500 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-600 disabled:opacity-50"
                  >
                    {loading ? 'Analyzing...' : 'Ask AI'}
                  </button>
                </div>

                {geminiResponse && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="font-medium text-green-800 mb-2">AI Response:</h4>
                    <div className="text-sm text-green-700 whitespace-pre-wrap">
                      {geminiResponse.response}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Reset Button */}
            {sessionId && (
              <div className="mt-8 pt-6 border-t border-gray-200">
                <button
                  onClick={resetApp}
                  className="bg-gray-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-600"
                >
                  Start New Analysis
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;