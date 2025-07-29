import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [uploadedData, setUploadedData] = useState(null);
  const [calculations, setCalculations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [days, setDays] = useState(30);
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [selectedPackaging, setSelectedPackaging] = useState([]);
  const [availableFilters, setAvailableFilters] = useState(null);
  const [geminiQuery, setGeminiQuery] = useState('');
  const [geminiResponse, setGeminiResponse] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [selectedCriticalItems, setSelectedCriticalItems] = useState([]);
  const [showCriticalOnly, setShowCriticalOnly] = useState(false);
  const fileInputRef = useRef(null);

  // Fetch available filters when session is created
  useEffect(() => {
    if (sessionId) {
      fetchFilters();
    }
  }, [sessionId]);

  const fetchFilters = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/filters/${sessionId}`);
      if (response.ok) {
        const filters = await response.json();
        setAvailableFilters(filters);
      }
    } catch (err) {
      console.error('Erreur lors de la récupération des filtres:', err);
    }
  };

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
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP! statut: ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setUploadedData(data);
      setAvailableFilters(data.filters);
      setActiveTab('calculate');
    } catch (err) {
      setError(`Échec du téléchargement: ${err.message}`);
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
          product_filter: selectedProducts.length > 0 ? selectedProducts : null,
          packaging_filter: selectedPackaging.length > 0 ? selectedPackaging : null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP! statut: ${response.status}`);
      }

      const data = await response.json();
      setCalculations(data);
      setSelectedCriticalItems([]);
      setActiveTab('results');
    } catch (err) {
      setError(`Échec du calcul: ${err.message}`);
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
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP! statut: ${response.status}`);
      }

      const data = await response.json();
      setGeminiResponse(data);
    } catch (err) {
      setError(`Échec de la requête IA: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCritical = async () => {
    if (!sessionId || selectedCriticalItems.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/export-critical/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          selected_items: selectedCriticalItems,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP! statut: ${response.status}`);
      }

      // Handle file download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `CBGS_Articles_Critiques_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setSelectedCriticalItems([]);
    } catch (err) {
      setError(`Échec de l'export: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetApp = () => {
    setSessionId(null);
    setUploadedData(null);
    setCalculations(null);
    setGeminiResponse(null);
    setAvailableFilters(null);
    setSelectedCriticalItems([]);
    setError(null);
    setActiveTab('upload');
    setDays(30);
    setSelectedProducts([]);
    setSelectedPackaging([]);
    setGeminiQuery('');
    setShowCriticalOnly(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleProductSelect = (product) => {
    setSelectedProducts(prev => 
      prev.includes(product) 
        ? prev.filter(p => p !== product)
        : [...prev, product]
    );
  };

  const handleProductSelectAll = () => {
    if (!availableFilters?.products) return;
    
    if (selectedProducts.length === availableFilters.products.length) {
      // If all are selected, deselect all
      setSelectedProducts([]);
    } else {
      // If not all are selected, select all
      setSelectedProducts([...availableFilters.products]);
    }
  };

  const handlePackagingSelect = (packaging) => {
    setSelectedPackaging(prev => 
      prev.includes(packaging) 
        ? prev.filter(p => p !== packaging)
        : [...prev, packaging]
    );
  };

  const handleCriticalItemSelect = (item) => {
    setSelectedCriticalItems(prev => {
      const exists = prev.find(i => i.id === item.id);
      if (exists) {
        return prev.filter(i => i.id !== item.id);
      } else {
        return [...prev, item];
      }
    });
  };

  const selectAllCritical = () => {
    if (!calculations) return;
    const criticalItems = calculations.calculations.filter(item => item.priority === 'high');
    setSelectedCriticalItems(criticalItems);
  };

  const clearCriticalSelection = () => {
    setSelectedCriticalItems([]);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const formatNumber = (num) => {
    if (typeof num === 'number') {
      return num.toLocaleString('fr-FR');
    }
    return num;
  };

  const getDisplayedCalculations = () => {
    if (!calculations) return [];
    if (showCriticalOnly) {
      return calculations.calculations.filter(item => item.priority === 'high');
    }
    return calculations.calculations;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg">
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Système de Gestion des Stocks - CBGS
            </h1>
            <p className="text-gray-600">
              Téléchargez des fichiers Excel pour analyser les niveaux de stock et calculer les besoins des dépôts
            </p>
          </div>

          <div className="p-6">
            {/* Tab Navigation */}
            <div className="flex space-x-4 mb-6">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'upload'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                📄 Télécharger Données
              </button>
              <button
                onClick={() => setActiveTab('calculate')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'calculate'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                } ${!sessionId ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={!sessionId}
              >
                🧮 Calculer Besoins
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'results'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                } ${!calculations ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={!calculations}
              >
                📊 Voir Résultats
              </button>
              <button
                onClick={() => setActiveTab('ai')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'ai'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                } ${!sessionId ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={!sessionId}
              >
                🤖 Analyses IA
              </button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                <div className="flex">
                  <span className="mr-2">❌</span>
                  <span>{error}</span>
                </div>
              </div>
            )}

            {/* Loading Display */}
            {loading && (
              <div className="mb-6 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded-lg">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-700 mr-2"></div>
                  <span>Traitement en cours...</span>
                </div>
              </div>
            )}

            {/* Upload Tab */}
            {activeTab === 'upload' && (
              <div className="space-y-6">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
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
                      Télécharger Fichier Excel
                    </div>
                    <div className="text-sm text-gray-500">
                      Choisissez un fichier .xlsx ou .xls avec les données de stock et de commande
                    </div>
                  </label>
                </div>

                {uploadedData && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h3 className="font-medium text-green-800 mb-2">✅ Téléchargement Réussi!</h3>
                    <div className="text-sm text-green-700 space-y-1">
                      <p>Enregistrements traités: <strong>{formatNumber(uploadedData.records_count)}</strong></p>
                      <p>Plage de dates: <strong>{uploadedData.date_range.start}</strong> à <strong>{uploadedData.date_range.end}</strong></p>
                      <p>Total des jours: <strong>{uploadedData.date_range.total_days}</strong></p>
                      <p>Dépôts: <strong>{uploadedData.filters.depots.length}</strong></p>
                      <p>Produits: <strong>{uploadedData.filters.products.length}</strong></p>
                      <p>Types d'emballage: <strong>{uploadedData.filters.packaging.length}</strong></p>
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
                      Jours à Couvrir
                    </label>
                    <input
                      type="number"
                      value={days}
                      onChange={(e) => setDays(e.target.value)}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      min="1"
                      max="365"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Filtrer par Produits ({selectedProducts.length} sélectionné{selectedProducts.length !== 1 ? 's' : ''})
                    </label>
                    <div className="max-h-40 overflow-y-auto border border-gray-300 rounded-lg p-2">
                      {availableFilters?.products?.map((product) => (
                        <label key={product} className="flex items-center space-x-2 py-1 hover:bg-gray-50 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedProducts.includes(product)}
                            onChange={() => handleProductSelect(product)}
                            className="rounded text-blue-500 focus:ring-blue-500"
                          />
                          <span className="text-sm text-gray-700">{product}</span>
                        </label>
                      ))}
                    </div>
                    {selectedProducts.length > 0 && (
                      <button
                        onClick={() => setSelectedProducts([])}
                        className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                      >
                        Effacer sélection
                      </button>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Filtrer par Emballage ({selectedPackaging.length} sélectionné{selectedPackaging.length !== 1 ? 's' : ''})
                    </label>
                    <div className="space-y-2">
                      {availableFilters?.packaging?.map((packaging) => (
                        <label key={packaging.value} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedPackaging.includes(packaging.value)}
                            onChange={() => handlePackagingSelect(packaging.value)}
                            className="rounded text-blue-500 focus:ring-blue-500"
                          />
                          <span className="text-sm text-gray-700">{packaging.display}</span>
                        </label>
                      ))}
                    </div>
                    {selectedPackaging.length > 0 && (
                      <button
                        onClick={() => setSelectedPackaging([])}
                        className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                      >
                        Effacer sélection
                      </button>
                    )}
                  </div>
                </div>

                <button
                  onClick={handleCalculate}
                  disabled={loading}
                  className="w-full bg-blue-500 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Calcul en cours...' : 'Calculer les Besoins'}
                </button>
              </div>
            )}

            {/* Results Tab */}
            {activeTab === 'results' && calculations && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {formatNumber(calculations.summary.total_depots)}
                    </div>
                    <div className="text-sm text-blue-700">Dépôts Totaux</div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {formatNumber(calculations.summary.total_products)}
                    </div>
                    <div className="text-sm text-green-700">Produits Totaux</div>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">
                      {formatNumber(calculations.summary.high_priority?.length || 0)}
                    </div>
                    <div className="text-sm text-red-700">Priorité Critique</div>
                  </div>
                  <div className="bg-yellow-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600">
                      {formatNumber(calculations.summary.medium_priority?.length || 0)}
                    </div>
                    <div className="text-sm text-yellow-700">Priorité Moyenne</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-gray-600">
                      {formatNumber(calculations.summary.no_stock_needed?.length || 0)}
                    </div>
                    <div className="text-sm text-gray-700">Stock Suffisant</div>
                  </div>
                </div>

                {/* Critical Items Selection */}
                {calculations.summary.high_priority.length > 0 && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-red-800">
                        🚨 Articles Critiques - Sélection pour Export
                      </h3>
                      <div className="flex items-center space-x-2">
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={showCriticalOnly}
                            onChange={(e) => setShowCriticalOnly(e.target.checked)}
                            className="rounded text-red-500 focus:ring-red-500"
                          />
                          <span className="text-sm text-red-700">Afficher uniquement les critiques</span>
                        </label>
                      </div>
                    </div>
                    <div className="flex space-x-4 mb-4">
                      <button
                        onClick={selectAllCritical}
                        className="bg-red-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-600 transition-colors"
                      >
                        Sélectionner tous les critiques
                      </button>
                      <button
                        onClick={clearCriticalSelection}
                        className="bg-gray-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-600 transition-colors"
                      >
                        Effacer sélection
                      </button>
                      <button
                        onClick={handleExportCritical}
                        disabled={selectedCriticalItems.length === 0 || loading}
                        className="bg-green-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        📄 Exporter CBGS ({selectedCriticalItems.length} sélectionnés)
                      </button>
                    </div>
                  </div>
                )}

                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border border-gray-300 rounded-lg">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="border border-gray-300 p-3 text-left">Sélection</th>
                        <th className="border border-gray-300 p-3 text-left">Dépôt</th>
                        <th className="border border-gray-300 p-3 text-left">Produit</th>
                        <th className="border border-gray-300 p-3 text-left">Emballage</th>
                        <th className="border border-gray-300 p-3 text-right">CQM</th>
                        <th className="border border-gray-300 p-3 text-right">Jours Couv.</th>
                        <th className="border border-gray-300 p-3 text-right">Stock Actuel</th>
                        <th className="border border-gray-300 p-3 text-right">Quantité à Envoyer</th>
                        <th className="border border-gray-300 p-3 text-center">Priorité</th>
                      </tr>
                    </thead>
                    <tbody>
                      {getDisplayedCalculations().map((item, index) => (
                        <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="border border-gray-300 p-3 text-center">
                            {item.priority === 'high' && (
                              <input
                                type="checkbox"
                                checked={selectedCriticalItems.some(selected => selected.id === item.id)}
                                onChange={() => handleCriticalItemSelect(item)}
                                className="rounded text-red-500 focus:ring-red-500"
                              />
                            )}
                          </td>
                          <td className="border border-gray-300 p-3 font-medium">{item.depot}</td>
                          <td className="border border-gray-300 p-3">{item.article_name}</td>
                          <td className="border border-gray-300 p-3">{item.packaging_type}</td>
                          <td className="border border-gray-300 p-3 text-right">{formatNumber(item.average_daily_consumption)}</td>
                          <td className="border border-gray-300 p-3 text-right">
                            <span className={item.priority === 'high' ? 'text-red-600 font-bold' : 
                                           item.priority === 'medium' ? 'text-yellow-600 font-bold' : ''}>
                              {formatNumber(item.days_of_coverage)}
                            </span>
                          </td>
                          <td className="border border-gray-300 p-3 text-right">{formatNumber(item.current_stock)}</td>
                          <td className="border border-gray-300 p-3 text-right">
                            <span className={item.quantity_to_send > 0 ? 'text-blue-600 font-bold' : 'text-gray-500'}>
                              {formatNumber(item.quantity_to_send)}
                            </span>
                          </td>
                          <td className="border border-gray-300 p-3 text-center">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(item.priority)}`}>
                              {item.priority_text}
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
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border border-blue-200">
                  <h3 className="font-medium text-blue-800 mb-2">🤖 Analyses Intelligentes</h3>
                  <p className="text-sm text-blue-700">
                    Posez des questions sur vos données. Les réponses seront brèves et directes.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => setGeminiQuery('Quels dépôts sont en rupture critique?')}
                    className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200"
                  >
                    <div className="font-medium text-gray-800">Dépôts critiques</div>
                    <div className="text-sm text-gray-600">Quels dépôts sont en rupture critique?</div>
                  </button>
                  <button
                    onClick={() => setGeminiQuery('Top 3 produits forte consommation?')}
                    className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200"
                  >
                    <div className="font-medium text-gray-800">Top consommation</div>
                    <div className="text-sm text-gray-600">Top 3 produits forte consommation?</div>
                  </button>
                  <button
                    onClick={() => setGeminiQuery('Anomalies dans les données?')}
                    className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200"
                  >
                    <div className="font-medium text-gray-800">Anomalies</div>
                    <div className="text-sm text-gray-600">Anomalies dans les données?</div>
                  </button>
                  <button
                    onClick={() => setGeminiQuery('Recommandations urgentes?')}
                    className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200"
                  >
                    <div className="font-medium text-gray-800">Recommandations</div>
                    <div className="text-sm text-gray-600">Recommandations urgentes?</div>
                  </button>
                </div>

                <div className="flex space-x-4">
                  <textarea
                    value={geminiQuery}
                    onChange={(e) => setGeminiQuery(e.target.value)}
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Posez une question brève..."
                    rows="2"
                  />
                  <button
                    onClick={handleGeminiQuery}
                    disabled={loading || !geminiQuery.trim()}
                    className="bg-green-500 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? 'Analyse...' : 'Analyser'}
                  </button>
                </div>

                {geminiResponse && (
                  <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
                    <h4 className="font-medium text-green-800 mb-3">🎯 Réponse Rapide:</h4>
                    <div className="text-sm text-green-700 leading-relaxed">
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
                  className="bg-gray-500 text-white px-6 py-2 rounded-lg font-medium hover:bg-gray-600 transition-colors"
                >
                  🔄 Nouvelle Analyse
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