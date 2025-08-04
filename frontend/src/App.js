import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [inventorySessionId, setInventorySessionId] = useState(null);
  const [uploadedData, setUploadedData] = useState(null);
  const [inventoryData, setInventoryData] = useState(null);
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
  const inventoryFileInputRef = useRef(null);

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

  const handleInventoryFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-inventory-excel`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP! statut: ${response.status}`);
      }

      const data = await response.json();
      setInventorySessionId(data.session_id);
      setInventoryData(data);
    } catch (err) {
      setError(`Échec du téléchargement d'inventaire: ${err.message}`);
    } finally {
      setLoading(false);
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
      const response = await fetch(`${API_BASE_URL}/api/enhanced-calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          days: parseInt(days),
          order_session_id: sessionId,
          inventory_session_id: inventorySessionId,
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
    setInventorySessionId(null);
    setUploadedData(null);
    setInventoryData(null);
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
    if (inventoryFileInputRef.current) {
      inventoryFileInputRef.current.value = '';
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
      // Round to 2 decimal places and use French locale formatting
      return Number(num.toFixed(2)).toLocaleString('fr-FR');
    }
    return num;
  };

  const getDisplayedCalculations = () => {
    if (!calculations) return [];
    if (showCriticalOnly) {
      return calculations.calculations.filter(item => item.priority === 'high');
    }
    
    // Ensure critical priority items always appear first
    const criticalItems = calculations.calculations.filter(item => item.priority === 'high');
    const otherItems = calculations.calculations.filter(item => item.priority !== 'high');
    
    return [...criticalItems, ...otherItems];
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
                  <span className="mr-2">ERREUR:</span>
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
                {/* Order Data Upload */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-800 mb-3">📊 1. Télécharger Données de Commandes</h3>
                  <div className="border-2 border-dashed border-blue-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="order-file-upload"
                    />
                    <label
                      htmlFor="order-file-upload"
                      className="cursor-pointer flex flex-col items-center space-y-2"
                    >
                      <div className="text-3xl text-blue-400">📈</div>
                      <div className="text-lg font-medium text-blue-700">
                        Fichier de Commandes Excel
                      </div>
                      <div className="text-sm text-blue-600">
                        Avec colonnes: Date de Commande, Article, Quantité Commandée, etc.
                      </div>
                    </label>
                  </div>

                  {uploadedData && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
                      <h4 className="font-medium text-green-800 mb-2">DONNÉES DE COMMANDES CHARGÉES</h4>
                      <div className="text-sm text-green-700 space-y-1">
                        <p>Enregistrements: <strong>{formatNumber(uploadedData.records_count)}</strong></p>
                        <p>Période: <strong>{uploadedData.date_range.start}</strong> à <strong>{uploadedData.date_range.end}</strong></p>
                        <p>Dépôts: <strong>{uploadedData.filters.depots.length}</strong> | Produits: <strong>{uploadedData.filters.products.length}</strong></p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Inventory Data Upload */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="font-medium text-green-800 mb-3">📦 2. Télécharger Données d'Inventaire</h3>
                  <div className="border-2 border-dashed border-green-300 rounded-lg p-6 text-center hover:border-green-400 transition-colors">
                    <input
                      ref={inventoryFileInputRef}
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={handleInventoryFileUpload}
                      className="hidden"
                      id="inventory-file-upload"
                    />
                    <label
                      htmlFor="inventory-file-upload"
                      className="cursor-pointer flex flex-col items-center space-y-2"
                    >
                      <div className="text-3xl text-green-400">🏪</div>
                      <div className="text-lg font-medium text-green-700">
                        Fichier d'Inventaire Excel
                      </div>
                      <div className="text-sm text-green-600">
                        Avec colonnes: Division, Article, Désignation article, STOCK À DATE
                      </div>
                    </label>
                  </div>

                  {inventoryData && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
                      <h4 className="font-medium text-green-800 mb-2">DONNÉES D'INVENTAIRE CHARGÉES</h4>
                      <div className="text-sm text-green-700 space-y-1">
                        <p>Enregistrements: <strong>{formatNumber(inventoryData.records_count)}</strong></p>
                        <p>Articles: <strong>{inventoryData.summary.articles_count}</strong></p>
                        <p>Stock Total: <strong>{formatNumber(inventoryData.summary.total_stock)}</strong></p>
                        <p>Divisions: <strong>{inventoryData.summary.divisions.join(', ')}</strong></p>
                      </div>
                    </div>
                  )}

                  {!inventoryData && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-4">
                      <p className="text-sm text-yellow-700">
                        💡 <strong>Recommandé:</strong> Téléchargez les données d'inventaire pour voir la disponibilité des stocks et identifier les articles manquants.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Calculate Tab */}
            {activeTab === 'calculate' && uploadedData && (
              <div className="space-y-6">
                {/* Status Overview */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-800 mb-2">ÉTAT DES DONNÉES</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="text-blue-600 font-medium">INFO</span>
                      <span>Données de commandes: <strong className="text-green-600">CHARGÉES</strong></span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">📦</span>
                      <span>Données d'inventaire: 
                        {inventoryData ? (
                          <strong className="text-green-600"> CHARGÉES</strong>
                        ) : (
                          <strong className="text-yellow-600"> NON CHARGÉES</strong>
                        )}
                      </span>
                    </div>
                  </div>
                  {inventoryData && (
                    <div className="mt-3 p-3 bg-green-100 rounded border border-green-300">
                      <p className="text-sm text-green-800">
                        🎯 <strong>Mode Avancé Activé:</strong> Le système vérifiera la disponibilité en inventaire pour chaque article demandé.
                      </p>
                    </div>
                  )}
                  {!inventoryData && (
                    <div className="mt-3 p-3 bg-yellow-100 rounded border border-yellow-300">
                      <p className="text-sm text-yellow-800">
                        💡 <strong>Mode Standard:</strong> Calculs basés uniquement sur les données de commandes. Pour vérifier la disponibilité, téléchargez les données d'inventaire.
                      </p>
                    </div>
                  )}
                </div>

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
                      {/* Select All Option */}
                      <label className="flex items-center space-x-2 py-1 hover:bg-gray-50 cursor-pointer border-b border-gray-200 mb-2">
                        <input
                          type="checkbox"
                          checked={selectedProducts.length === availableFilters?.products?.length && availableFilters?.products?.length > 0}
                          onChange={handleProductSelectAll}
                          className="rounded text-blue-500 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-blue-700">Sélectionner tout</span>
                      </label>
                      
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
                {/* Summary Statistics */}
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

                {/* Inventory Status Summary */}
                {calculations.summary.inventory_status === 'available' && (
                  <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-4">
                    <h3 className="font-medium text-green-800 mb-3">📦 État de l'Inventaire</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl font-bold text-green-600">STOCK</span>
                        <div>
                          <div className="font-bold text-green-600">
                            {formatNumber(calculations.summary.sufficient_items || 0)}
                          </div>
                          <div className="text-green-700">Stock Suffisant</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl font-bold text-yellow-600">[!]</span>
                        <div>
                          <div className="font-bold text-yellow-600">
                            {formatNumber(calculations.summary.partial_items || 0)}
                          </div>
                          <div className="text-yellow-700">Stock Partiel</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl font-bold text-red-600">[X]</span>
                        <div>
                          <div className="font-bold text-red-600">
                            {formatNumber(calculations.summary.insufficient_items || 0)}
                          </div>
                          <div className="text-red-700">Stock Insuffisant</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl font-bold text-gray-600">[?]</span>
                        <div>
                          <div className="font-bold text-gray-600">
                            {formatNumber(calculations.summary.not_found_items || 0)}
                          </div>
                          <div className="text-gray-700">Non Trouvé</div>
                        </div>
                      </div>
                    </div>
                    {calculations.summary.total_inventory_shortage > 0 && (
                      <div className="mt-3 p-3 bg-red-100 rounded border border-red-300">
                        <p className="text-sm text-red-800">
                          🚨 <strong>Manque Total:</strong> {formatNumber(calculations.summary.total_inventory_shortage)} unités manquantes en inventaire.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Sourcing Summary */}
                {calculations.summary.sourcing_summary && (
                  <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-medium text-blue-800 mb-3">🏭 Analyse du Sourcing</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">🏭</span>
                        <div>
                          <div className="font-bold text-green-600">
                            {formatNumber(calculations.summary.sourcing_summary.local_items || 0)}
                          </div>
                          <div className="text-green-700">Production Locale</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">🌍</span>
                        <div>
                          <div className="font-bold text-orange-600">
                            {formatNumber(calculations.summary.sourcing_summary.external_items || 0)}
                          </div>
                          <div className="text-orange-700">Sourcing Externe</div>
                        </div>
                      </div>
                    </div>
                    {calculations.summary.sourcing_summary.external_items > 0 && (
                      <div className="mt-3 p-3 bg-orange-100 rounded border border-orange-300">
                        <p className="text-sm text-orange-800">
                          [!] <strong>Attention:</strong> {calculations.summary.sourcing_summary.external_items} article(s) nécessitent un sourcing externe.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Delivery Optimization Summary */}
                {calculations.summary.delivery_optimization && (
                  <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
                    <h3 className="font-medium text-purple-800 mb-3">🚛 Optimisation des Livraisons (Contrainte 20 Palettes)</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl font-bold text-green-600">[OK]</span>
                        <div>
                          <div className="font-bold text-green-600">
                            {formatNumber(calculations.summary.delivery_optimization.efficient_depots || 0)}
                          </div>
                          <div className="text-green-700">Dépôts Efficaces</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl font-bold text-yellow-600">[!]</span>
                        <div>
                          <div className="font-bold text-orange-600">
                            {formatNumber(calculations.summary.delivery_optimization.inefficient_depots || 0)}
                          </div>
                          <div className="text-orange-700">Dépôts Inefficaces</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">📦</span>
                        <div>
                          <div className="font-bold text-blue-600">
                            {formatNumber(calculations.summary.delivery_optimization.total_palettes || 0)}
                          </div>
                          <div className="text-blue-700">Total Palettes</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">🎯</span>
                        <div>
                          <div className="font-bold text-purple-600">20</div>
                          <div className="text-purple-700">Min. par Dépôt</div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Depot Details */}
                    {calculations.summary.delivery_optimization.depot_summaries && calculations.summary.delivery_optimization.depot_summaries.length > 0 && (
                      <div className="mt-4">
                        <h4 className="font-medium text-purple-800 mb-2">Détail par Dépôt:</h4>
                        <div className="space-y-2">
                          {calculations.summary.delivery_optimization.depot_summaries.map((depot, index) => (
                            <div key={index} className={`p-3 rounded-lg border ${
                              depot.delivery_status === 'efficient' 
                                ? 'bg-green-50 border-green-200' 
                                : 'bg-orange-50 border-orange-200'
                            }`}>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                  <span className={`text-lg ${
                                    depot.delivery_status === 'efficient' ? 'text-green-600' : 'text-orange-600'
                                  }`}>
                                    {depot.delivery_status === 'efficient' ? '[OK]' : '[!]'}
                                  </span>
                                  <span className="font-medium">{depot.depot_name}</span>
                                  <span className={`text-sm px-2 py-1 rounded ${
                                    depot.delivery_status === 'efficient'
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-orange-100 text-orange-800'
                                  }`}>
                                    {depot.total_palettes} palettes
                                  </span>
                                </div>
                                <div className="text-sm text-gray-600">
                                  {depot.items_count} article{depot.items_count !== 1 ? 's' : ''}
                                </div>
                              </div>
                              
                              {/* Suggestions for inefficient depots */}
                              {depot.delivery_status === 'inefficient' && depot.suggested_items && depot.suggested_items.length > 0 && (
                                <div className="mt-3 p-2 bg-white rounded border">
                                  <div className="text-sm font-medium text-orange-800 mb-2">
                                    💡 Suggestions pour atteindre 20 palettes ({depot.palettes_needed} palettes manquantes):
                                  </div>
                                  <div className="space-y-1">
                                    {depot.suggested_items.slice(0, 3).map((suggestion, sugIndex) => (
                                      <div key={sugIndex} className="text-xs text-gray-700 flex justify-between">
                                        <span>{suggestion.article_code} - {suggestion.packaging_type}</span>
                                        <span className="font-medium">
                                          {formatNumber(suggestion.quantity_to_send)} unités ({suggestion.palette_quantity} pal.)
                                        </span>
                                      </div>
                                    ))}
                                    {depot.suggested_items.length > 3 && (
                                      <div className="text-xs text-gray-500 italic">
                                        ... et {depot.suggested_items.length - 3} autre(s) suggestion(s)
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {calculations.summary.delivery_optimization.inefficient_depots > 0 && (
                      <div className="mt-3 p-3 bg-orange-100 rounded border border-orange-300">
                        <p className="text-sm text-orange-800">
                          🚛 <strong>Optimisation:</strong> {calculations.summary.delivery_optimization.inefficient_depots} dépôt(s) n'atteignent pas le minimum de 20 palettes. 
                          Considérez ajouter les articles suggérés pour optimiser les coûts de livraison.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {calculations.summary.inventory_status === 'no_inventory_data' && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-sm text-yellow-800">
                      💡 <strong>Info:</strong> Aucune donnée d'inventaire disponible. Les calculs sont basés uniquement sur les données de commandes.
                    </p>
                  </div>
                )}

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
                        <th className="border border-gray-300 p-3 text-left">Code Article</th>
                        <th className="border border-gray-300 p-3 text-left">Emballage</th>
                        <th className="border border-gray-300 p-3 text-right">CQM</th>
                        <th className="border border-gray-300 p-3 text-right">Jours Couv.</th>
                        <th className="border border-gray-300 p-3 text-right">Stock Actuel</th>
                        <th className="border border-gray-300 p-3 text-right">Quantité à Envoyer</th>
                        <th className="border border-gray-300 p-3 text-right">Palettes</th>
                        {calculations.summary.inventory_status === 'available' && (
                          <>
                            <th className="border border-gray-300 p-3 text-right">Stock Inventaire</th>
                            <th className="border border-gray-300 p-3 text-center">Disponibilité</th>
                          </>
                        )}
                        <th className="border border-gray-300 p-3 text-center">Sourcing</th>
                        <th className="border border-gray-300 p-3 text-center">Livraison</th>
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
                          <td className="border border-gray-300 p-3">{item.article_code}</td>
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
                          <td className="border border-gray-300 p-3 text-right">
                            <span className={`font-medium ${
                              item.palette_quantity > 0 
                                ? item.delivery_efficient 
                                  ? 'text-green-600' 
                                  : 'text-orange-600'
                                : 'text-gray-500'
                            }`}>
                              {item.palette_quantity || 0}
                            </span>
                          </td>
                          {calculations.summary.inventory_status === 'available' && (
                            <>
                              <td className="border border-gray-300 p-3 text-right">
                                <span className="font-medium">
                                  {item.inventory_available !== undefined ? formatNumber(item.inventory_available) : '-'}
                                </span>
                                {item.inventory_shortage > 0 && (
                                  <div className="text-xs text-red-600 mt-1">
                                    Manque: {formatNumber(item.inventory_shortage)}
                                  </div>
                                )}
                              </td>
                              <td className="border border-gray-300 p-3 text-center">
                                {item.inventory_status && (
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.inventory_status_color}`}>
                                    {item.inventory_status_text}
                                  </span>
                                )}
                              </td>
                            </>
                          )}
                          <td className="border border-gray-300 p-3 text-center">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              item.is_locally_made 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-orange-100 text-orange-800'
                            }`}>
                              {item.sourcing_text || (item.is_locally_made ? 'Production Locale' : 'Sourcing Externe')}
                            </span>
                          </td>
                          <td className="border border-gray-300 p-3 text-center">
                            {item.delivery_status && (
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.delivery_status_color}`}>
                                {item.delivery_efficient ? '[OK] Efficace' : '[!] Inefficace'}
                              </span>
                            )}
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
                  <h3 className="font-medium text-blue-800 mb-2">🤖 Assistant Intelligent d'Analyse des Stocks</h3>
                  <p className="text-sm text-blue-700">
                    Analysez vos données journalières de stock avec des insights précis et des recommandations d'expert.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => setGeminiQuery('Quels dépôts ont les plus faibles niveaux de stock aujourd\'hui?')}
                    className="p-4 text-left bg-red-50 hover:bg-red-100 rounded-lg border border-red-200 transition-colors"
                  >
                    <div className="font-medium text-red-800 flex items-center">
                      🚨 <span className="ml-2">Stocks Critiques</span>
                    </div>
                    <div className="text-sm text-red-600 mt-1">Dépôts avec faibles stocks</div>
                  </button>
                  
                  <button
                    onClick={() => setGeminiQuery('Quels sont les 5 produits les plus commandés aujourd\'hui?')}
                    className="p-4 text-left bg-orange-50 hover:bg-orange-100 rounded-lg border border-orange-200 transition-colors"
                  >
                    <div className="font-medium text-orange-800 flex items-center">
                      📈 <span className="ml-2">Top Commandes</span>
                    </div>
                    <div className="text-sm text-orange-600 mt-1">Produits les plus demandés</div>
                  </button>
                  
                  <button
                    onClick={() => setGeminiQuery('Analysez la répartition des commandes par dépôt pour aujourd\'hui.')}
                    className="p-4 text-left bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors"
                  >
                    <div className="font-medium text-blue-800 flex items-center">
                      📊 <span className="ml-2">Répartition Dépôts</span>
                    </div>
                    <div className="text-sm text-blue-600 mt-1">Volume par dépôt</div>
                  </button>
                  
                  <button
                    onClick={() => setGeminiQuery('Quels produits nécessitent un réapprovisionnement immédiat basé sur les stocks actuels?')}
                    className="p-4 text-left bg-green-50 hover:bg-green-100 rounded-lg border border-green-200 transition-colors"
                  >
                    <div className="font-medium text-green-800 flex items-center">
                      💡 <span className="ml-2">Réapprovisionnement</span>
                    </div>
                    <div className="text-sm text-green-600 mt-1">Actions urgentes</div>
                  </button>
                  
                  <button
                    onClick={() => setGeminiQuery('Comparez les volumes commandés par type d\'emballage aujourd\'hui.')}
                    className="p-4 text-left bg-indigo-50 hover:bg-indigo-100 rounded-lg border border-indigo-200 transition-colors"
                  >
                    <div className="font-medium text-indigo-800 flex items-center">
                      📦 <span className="ml-2">Analyse Emballages</span>
                    </div>
                    <div className="text-sm text-indigo-600 mt-1">Volumes par packaging</div>
                  </button>
                  
                  <button
                    onClick={() => setGeminiQuery('Donnez-moi un résumé des performances commerciales du jour avec les chiffres clés.')}
                    className="p-4 text-left bg-purple-50 hover:bg-purple-100 rounded-lg border border-purple-200 transition-colors"
                  >
                    <div className="font-medium text-purple-800 flex items-center">
                      📈 <span className="ml-2">Résumé Journalier</span>
                    </div>
                    <div className="text-sm text-purple-600 mt-1">Performance du jour</div>
                  </button>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex space-x-4">
                    <textarea
                      value={geminiQuery}
                      onChange={(e) => setGeminiQuery(e.target.value)}
                      className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      placeholder="Posez votre question personnalisée sur les données de stock..."
                      rows="3"
                    />
                    <button
                      onClick={handleGeminiQuery}
                      disabled={loading || !geminiQuery.trim()}
                      className="bg-blue-500 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-start"
                    >
                      {loading ? (
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Analyse...</span>
                        </div>
                      ) : (
                        '🔍 Analyser'
                      )}
                    </button>
                  </div>
                </div>

                {geminiResponse && (
                  <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
                    <h4 className="font-medium text-green-800 mb-3 flex items-center">
                      🎯 <span className="ml-2">Analyse Experte:</span>
                    </h4>
                    <div className="text-sm text-green-700 leading-relaxed bg-white p-4 rounded border">
                      {geminiResponse.response}
                    </div>
                    <div className="mt-3 text-xs text-green-600">
                      Question analysée: "{geminiResponse.query}"
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