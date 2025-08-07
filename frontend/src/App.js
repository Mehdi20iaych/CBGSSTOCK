import React, { useState, useRef } from 'react';
import './App.css';
import { 
  DocumentIcon, 
  ChartBarIcon, 
  ArrowTrendingUpIcon,
  ArchiveBoxIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ClipboardDocumentListIcon,
  TruckIcon,
  ChevronRightIcon,
  LightBulbIcon,
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon
} from '@heroicons/react/24/outline';

// Use same origin for API calls - all backend calls go through /api prefix
const API_BASE_URL = window.location.origin;

function App() {
  // États pour les données uploadées
  const [commandesData, setCommandesData] = useState(null);
  const [stockData, setStockData] = useState(null);
  const [transitData, setTransitData] = useState(null);
  
  // États pour les calculs et interface
  const [calculations, setCalculations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [days, setDays] = useState(10);
  const [activeTab, setActiveTab] = useState('upload');
  const [selectedItems, setSelectedItems] = useState([]);
  
  // États pour les filtres
  const [availablePackaging, setAvailablePackaging] = useState([]);
  const [selectedPackaging, setSelectedPackaging] = useState([]);
  
  // États pour les suggestions de palettes
  const [suggestions, setSuggestions] = useState({});
  const [loadingSuggestions, setLoadingSuggestions] = useState({});
  const [showSuggestions, setShowSuggestions] = useState({});
  
  // États pour le chat IA
  const [chatMessages, setChatMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  
  // Références pour les inputs de fichiers
  const commandesFileRef = useRef(null);
  const stockFileRef = useRef(null);
  const transitFileRef = useRef(null);

  // Upload fichier commandes
  const handleCommandesFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-commandes-excel`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP! statut: ${response.status}`);
      }

      const data = await response.json();
      setCommandesData(data);
      
      // Mettre à jour les filtres d'emballage disponibles
      if (data.filters && data.filters.packaging) {
        setAvailablePackaging(data.filters.packaging);
        // Par défaut, sélectionner tous les types d'emballage
        setSelectedPackaging(data.filters.packaging);
      }
      
      setError(null);
    } catch (err) {
      setError(`Échec du téléchargement des commandes: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Upload fichier stock
  const handleStockFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-stock-excel`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP! statut: ${response.status}`);
      }

      const data = await response.json();
      setStockData(data);
      setError(null);
    } catch (err) {
      setError(`Échec du téléchargement du stock: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Upload fichier transit
  const handleTransitFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-transit-excel`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP! statut: ${response.status}`);
      }

      const data = await response.json();
      setTransitData(data);
      setError(null);
    } catch (err) {
      setError(`Échec du téléchargement des données de transit: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Lancer les calculs
  const handleCalculate = async () => {
    if (!commandesData) {
      setError('Veuillez d\'abord uploader un fichier de commandes');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          days: days,
          packaging_filter: selectedPackaging.length > 0 ? selectedPackaging : null
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors du calcul');
      }

      const data = await response.json();
      setCalculations(data);
      setActiveTab('results');
    } catch (err) {
      setError(`Erreur de calcul: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Export Excel
  const handleExportExcel = async () => {
    if (!selectedItems.length) {
      setError('Veuillez sélectionner au moins un élément à exporter');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/export-excel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          selected_items: selectedItems,
          session_id: 'current'
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de l\'export');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `Calcul_Stock_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Erreur d'export: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Gérer la sélection des items
  const handleItemSelection = (item) => {
    setSelectedItems(prev => {
      const exists = prev.some(i => i.article === item.article && i.depot === item.depot && i.packaging === item.packaging);
      if (exists) {
        return prev.filter(i => !(i.article === item.article && i.depot === item.depot && i.packaging === item.packaging));
      } else {
        return [...prev, item];
      }
    });
  };

  // Sélectionner tous les items
  const handleSelectAll = () => {
    if (calculations && calculations.calculations) {
      if (selectedItems.length === calculations.calculations.length) {
        setSelectedItems([]);
      } else {
        setSelectedItems([...calculations.calculations]);
      }
    }
  };

  // Gérer la sélection des filtres d'emballage
  const handlePackagingFilter = (packaging) => {
    setSelectedPackaging(prev => {
      if (prev.includes(packaging)) {
        return prev.filter(p => p !== packaging);
      } else {
        return [...prev, packaging];
      }
    });
  };

  // Sélectionner tous/aucun emballages
  const handleSelectAllPackaging = () => {
    if (selectedPackaging.length === availablePackaging.length) {
      setSelectedPackaging([]);
    } else {
      setSelectedPackaging([...availablePackaging]);
    }
  };

  // Obtenir l'icône de statut
  const getStatusIcon = (status) => {
    switch (status) {
      case 'OK':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'À livrer':
        return <ExclamationTriangleIcon className="w-5 h-5 text-orange-500" />;
      case 'Non couvert':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  // Obtenir des suggestions pour compléter les palettes d'un dépôt
  const fetchDepotSuggestions = async (depotName) => {
    setLoadingSuggestions(prev => ({ ...prev, [depotName]: true }));
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/depot-suggestions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          depot_name: depotName,
          days: days
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la récupération des suggestions');
      }

      const data = await response.json();
      setSuggestions(prev => ({ ...prev, [depotName]: data }));
      setShowSuggestions(prev => ({ ...prev, [depotName]: true }));
    } catch (err) {
      setError(`Erreur lors de la récupération des suggestions: ${err.message}`);
    } finally {
      setLoadingSuggestions(prev => ({ ...prev, [depotName]: false }));
    }
  };

  // Basculer l'affichage des suggestions
  const toggleSuggestions = (depotName) => {
    if (showSuggestions[depotName]) {
      setShowSuggestions(prev => ({ ...prev, [depotName]: false }));
    } else if (suggestions[depotName]) {
      setShowSuggestions(prev => ({ ...prev, [depotName]: true }));
    } else {
      fetchDepotSuggestions(depotName);
    }
  };

  // Vérifier si un dépôt a des camions incomplets (pas un multiple parfait de 24 palettes)
  const hasIncompletetrucks = (depot) => {
    return depot.total_palettes > 0 && depot.total_palettes % 24 !== 0;
  };

  // Fonctions pour le chat IA
  const handleSendMessage = async () => {
    if (!currentMessage.trim() || chatLoading) return;

    const userMessage = currentMessage.trim();
    setCurrentMessage('');
    setChatLoading(true);

    // Ajouter le message utilisateur
    const newUserMessage = {
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    setChatMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la communication avec l\'IA');
      }

      const data = await response.json();

      // Mettre à jour l'ID de conversation
      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      // Ajouter la réponse de l'IA
      const aiMessage = {
        type: 'ai',
        content: data.response,
        timestamp: new Date(),
        hasData: data.has_data,
        dataTypes: data.data_types || []
      };
      setChatMessages(prev => [...prev, aiMessage]);

    } catch (err) {
      const errorMessage = {
        type: 'error',
        content: `Erreur: ${err.message}`,
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setChatMessages([]);
    setConversationId(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <ArchiveBoxIcon className="w-8 h-8 mr-3 text-blue-600" />
              Gestion des Stocks - Version Simplifiée
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Calculez automatiquement les quantités à envoyer depuis M210
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'upload'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <DocumentIcon className="w-5 h-5 inline mr-2" />
            Upload des Fichiers
          </button>
          <button
            onClick={() => setActiveTab('calculate')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'calculate'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <ChartBarIcon className="w-5 h-5 inline mr-2" />
            Calculs
          </button>
          <button
            onClick={() => setActiveTab('results')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'results'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <ArrowTrendingUpIcon className="w-5 h-5 inline mr-2" />
            Résultats
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'chat'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <ChatBubbleLeftRightIcon className="w-5 h-5 inline mr-2" />
            Chat IA
          </button>
        </nav>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Affichage des erreurs */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
            <div className="flex">
              <XCircleIcon className="w-5 h-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Tab Upload */}
        {activeTab === 'upload' && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium mb-4 flex items-center">
                <DocumentIcon className="w-6 h-6 mr-2 text-blue-600" />
                Upload des Fichiers Excel
              </h2>

              <div className="grid md:grid-cols-3 gap-6">
                {/* Fichier Commandes */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-gray-400 transition-colors">
                  <div className="text-center">
                    <DocumentIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">Fichier Commandes</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Colonnes: B(Article), D(Point d'Expédition), F(Quantité Commandée), G(Stock Utilisation Libre), I(Type Emballage)
                    </p>
                    <div className="mt-4">
                      <input
                        type="file"
                        ref={commandesFileRef}
                        onChange={handleCommandesFileUpload}
                        accept=".xlsx,.xls"
                        className="hidden"
                      />
                      <button
                        onClick={() => commandesFileRef.current?.click()}
                        disabled={loading}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                      >
                        Choisir un fichier
                      </button>
                    </div>
                    {commandesData && (
                      <div className="mt-3 text-sm">
                        <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          ✓ {commandesData.summary.total_records} enregistrements
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Fichier Stock */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-gray-400 transition-colors">
                  <div className="text-center">
                    <ArchiveBoxIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">Fichier Stock M210</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Colonnes: A(Division), B(Article), D(STOCK À DATE)
                    </p>
                    <div className="mt-4">
                      <input
                        type="file"
                        ref={stockFileRef}
                        onChange={handleStockFileUpload}
                        accept=".xlsx,.xls"
                        className="hidden"
                      />
                      <button
                        onClick={() => stockFileRef.current?.click()}
                        disabled={loading}
                        className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                      >
                        Choisir un fichier
                      </button>
                    </div>
                    {stockData && (
                      <div className="mt-3 text-sm">
                        <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          ✓ {stockData.summary.unique_articles} articles
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Fichier Transit */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-gray-400 transition-colors">
                  <div className="text-center">
                    <ArrowTrendingUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">Fichier Transit</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Colonnes: A(Article), C(Division), G(Division cédante), I(Quantité)
                    </p>
                    <div className="mt-4">
                      <input
                        type="file"
                        ref={transitFileRef}
                        onChange={handleTransitFileUpload}
                        accept=".xlsx,.xls"
                        className="hidden"
                      />
                      <button
                        onClick={() => transitFileRef.current?.click()}
                        disabled={loading}
                        className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                      >
                        Choisir un fichier
                      </button>
                    </div>
                    {transitData && (
                      <div className="mt-3 text-sm">
                        <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          ✓ {transitData.summary.total_records} enregistrements
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 className="text-sm font-medium text-blue-900">Instructions :</h4>
                <ul className="mt-2 text-sm text-blue-800 list-disc list-inside space-y-1">
                  <li>Le fichier <strong>Commandes</strong> est obligatoire</li>
                  <li>Les fichiers <strong>Stock M210</strong> et <strong>Transit</strong> sont optionnels mais recommandés</li>
                  <li>Respectez exactement les colonnes spécifiées pour chaque fichier</li>
                  <li>Colonne I doit contenir le type d'emballage (verre, pet, ciel)</li>
                  <li>Seuls les dépôts différents de M210 seront approvisionnés</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Tab Calculate */}
        {activeTab === 'calculate' && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium mb-4 flex items-center">
              <ChartBarIcon className="w-6 h-6 mr-2 text-blue-600" />
              Configuration des Calculs
            </h2>

            <div className="max-w-2xl space-y-6">
              <div>
                <label htmlFor="days" className="block text-sm font-medium text-gray-700">
                  Nombre de jours à couvrir
                </label>
                <input
                  type="number"
                  id="days"
                  value={days}
                  onChange={(e) => setDays(parseInt(e.target.value) || 10)}
                  min="1"
                  max="365"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              {/* Filtre Type d'Emballage */}
              {availablePackaging.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Types d'emballage à inclure
                  </label>
                  <div className="space-y-2">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="select-all-packaging"
                        checked={selectedPackaging.length === availablePackaging.length}
                        onChange={handleSelectAllPackaging}
                        className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                      <label htmlFor="select-all-packaging" className="ml-2 text-sm text-gray-700 font-medium">
                        Tout sélectionner
                      </label>
                    </div>
                    <div className="grid grid-cols-3 gap-3 mt-3">
                      {availablePackaging.map((packaging) => (
                        <div key={packaging} className="flex items-center">
                          <input
                            type="checkbox"
                            id={`packaging-${packaging}`}
                            checked={selectedPackaging.includes(packaging)}
                            onChange={() => handlePackagingFilter(packaging)}
                            className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                          />
                          <label htmlFor={`packaging-${packaging}`} className="ml-2 text-sm text-gray-700 capitalize">
                            {packaging}
                          </label>
                        </div>
                      ))}
                    </div>
                    {selectedPackaging.length === 0 && (
                      <p className="text-sm text-amber-600">
                        ⚠️ Aucun type d'emballage sélectionné - veuillez en choisir au moins un
                      </p>
                    )}
                  </div>
                </div>
              )}

              <div className="pt-4">
                <button
                  onClick={handleCalculate}
                  disabled={loading || !commandesData || selectedPackaging.length === 0}
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Calcul en cours...
                    </>
                  ) : (
                    <>
                      <ChartBarIcon className="w-5 h-5 mr-2" />
                      Lancer les Calculs
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
              <h4 className="text-sm font-medium text-yellow-900">Formule appliquée :</h4>
              <p className="mt-2 text-sm text-yellow-800">
                <strong>Quantité à Envoyer = max(0, (Quantité Commandée × Jours à Couvrir) - Stock Utilisation Libre - Quantité en Transit)</strong>
              </p>
            </div>
          </div>
        )}

        {/* Tab Results */}
        {activeTab === 'results' && calculations && (
          <div className="space-y-6">
            {/* Résumé */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium mb-4 flex items-center">
                <ClipboardDocumentListIcon className="w-6 h-6 mr-2 text-blue-600" />
                Résumé des Calculs
              </h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">{calculations.summary.total_items}</div>
                  <div className="text-sm text-gray-600">Total Items</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{calculations.summary.items_ok}</div>
                  <div className="text-sm text-green-600">OK</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">{calculations.summary.items_a_livrer}</div>
                  <div className="text-sm text-orange-600">À Livrer</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{calculations.summary.items_non_couverts}</div>
                  <div className="text-sm text-red-600">Non Couvert</div>
                </div>
              </div>

              {/* Sourcing Summary */}
              {calculations.sourcing_summary && (
                <div className="border-t pt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Analyse Sourcing</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-lg font-semibold text-slate-700">{calculations.sourcing_summary.local_items}</div>
                      <div className="text-xs text-slate-600">Production Locale</div>
                      <div className="text-xs text-slate-500">({calculations.sourcing_summary.local_percentage}%)</div>
                    </div>
                    <div className="text-center p-3 bg-amber-50 rounded-lg border border-amber-200">
                      <div className="text-lg font-semibold text-amber-700">{calculations.sourcing_summary.external_items}</div>
                      <div className="text-xs text-amber-600">Sourcing Externe</div>
                      <div className="text-xs text-amber-500">({calculations.sourcing_summary.external_percentage}%)</div>
                    </div>
                  </div>
                  {calculations.sourcing_summary.external_items > 0 && (
                    <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <p className="text-sm text-amber-700">
                        ⚠️ {calculations.sourcing_summary.external_items} produit(s) nécessitent un sourcing externe
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Depot Summary */}
              {calculations.depot_summary && calculations.depot_summary.length > 0 && (
                <div className="border-t pt-4 mt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                    <TruckIcon className="w-4 h-4 mr-2" />
                    Logistique par Dépôt
                  </h3>
                  <div className="space-y-3">
                    {calculations.depot_summary.map((depot, index) => (
                      <div key={index}>
                        <div className={`p-3 rounded-lg border ${
                          depot.delivery_efficiency === 'Efficace' 
                            ? 'bg-green-50 border-green-200' 
                            : 'bg-orange-50 border-orange-200'
                        }`}>
                          <div className="flex justify-between items-center">
                            <div className="flex items-center space-x-4">
                              <span className="font-medium text-gray-900">{depot.depot}</span>
                              <div className="flex items-center space-x-2 text-sm">
                                <span className="text-gray-600">{depot.total_palettes} palettes</span>
                                <span className="text-gray-400">•</span>
                                <span className="text-gray-600">{depot.trucks_needed} camion(s)</span>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                depot.delivery_efficiency === 'Efficace' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-orange-100 text-orange-800'
                              }`}>
                                {depot.delivery_efficiency}
                              </span>
                              {/* Arrow icon for suggestions */}
                              {hasIncompletetrucks(depot) && (
                                <button
                                  onClick={() => toggleSuggestions(depot.depot)}
                                  className={`p-1 rounded transition-colors ${
                                    depot.delivery_efficiency === 'Efficace'
                                      ? 'text-blue-600 hover:text-blue-800 hover:bg-blue-100'
                                      : 'text-orange-600 hover:text-orange-800 hover:bg-orange-100'
                                  }`}
                                  title="Voir les suggestions pour compléter des camions complets (24 palettes)"
                                  disabled={loadingSuggestions[depot.depot]}
                                >
                                  {loadingSuggestions[depot.depot] ? (
                                    <div className={`w-4 h-4 border-2 border-t-transparent rounded-full animate-spin ${
                                      depot.delivery_efficiency === 'Efficace'
                                        ? 'border-blue-600'
                                        : 'border-orange-600'
                                    }`} />
                                  ) : (
                                    <ChevronRightIcon className={`w-4 h-4 transition-transform ${
                                      showSuggestions[depot.depot] ? 'rotate-90' : ''
                                    }`} />
                                  )}
                                </button>
                              )}
                            </div>
                          </div>
                          {hasIncompletetrucks(depot) && (
                            <div className={`mt-2 text-xs ${
                              depot.delivery_efficiency === 'Efficace'
                                ? 'text-blue-700'
                                : 'text-orange-700'
                            }`}>
                              {depot.delivery_efficiency === 'Efficace' 
                                ? '💡 Optimisation possible: camion incomplet détecté'
                                : '⚠️ Livraison inefficace: camion(s) incomplet(s)'
                              }
                            </div>
                          )}
                        </div>

                        {/* Suggestions panel */}
                        {showSuggestions[depot.depot] && suggestions[depot.depot] && (
                          <div className="mt-2 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <div className="flex items-center mb-3">
                              <LightBulbIcon className="w-4 h-4 mr-2 text-blue-600" />
                              <span className="text-sm font-medium text-blue-800">
                                Suggestions pour {depot.depot}
                              </span>
                            </div>
                            
                            <div className="text-xs text-blue-700 mb-3">
                              Palettes actuelles: <strong>{suggestions[depot.depot].current_palettes}</strong> → 
                              Objectif: <strong>{suggestions[depot.depot].target_palettes}</strong> palettes 
                              ({suggestions[depot.depot].palettes_to_add} palettes à ajouter)
                            </div>

                            {suggestions[depot.depot].suggestions && suggestions[depot.depot].suggestions.length > 0 ? (
                              <div className="space-y-2">
                                {suggestions[depot.depot].suggestions.map((suggestion, idx) => (
                                  <div key={idx} className={`p-2 rounded border text-xs ${
                                    suggestion.can_fulfill 
                                      ? 'bg-green-50 border-green-200' 
                                      : 'bg-red-50 border-red-200'
                                  }`}>
                                    <div className="flex justify-between items-start">
                                      <div>
                                        <div className="font-medium text-gray-900">
                                          Article: {suggestion.article} ({suggestion.packaging})
                                        </div>
                                        <div className="text-gray-600 mt-1">
                                          Stock M210: {suggestion.stock_m210} unités
                                        </div>
                                        <div className="text-blue-700 font-medium">
                                          Suggestion: {suggestion.suggested_quantity} produits 
                                          ({suggestion.suggested_palettes} palette{suggestion.suggested_palettes > 1 ? 's' : ''})
                                        </div>
                                        {suggestion.reason && (
                                          <div className="text-orange-600 text-xs mt-1">
                                            {suggestion.reason}
                                          </div>
                                        )}
                                      </div>
                                      <div className="ml-2">
                                        <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                                          suggestion.can_fulfill
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-red-100 text-red-800'
                                        }`}>
                                          {suggestion.feasibility}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs text-gray-600">
                                {suggestions[depot.depot].message || 'Aucune suggestion disponible'}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Tableau des résultats */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">Détail des Calculs</h3>
                <div className="flex space-x-3">
                  <button
                    onClick={handleSelectAll}
                    className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    {selectedItems.length === calculations.calculations.length ? 'Tout désélectionner' : 'Tout sélectionner'}
                  </button>
                  <button
                    onClick={handleExportExcel}
                    disabled={selectedItems.length === 0 || loading}
                    className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    Exporter Excel ({selectedItems.length})
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input type="checkbox" className="rounded" />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code Article</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code Dépôt</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type Emballage</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantité Commandée</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock Actuel</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantité en Transit</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantité à Envoyer</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Palettes</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock Dispo M210</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sourcing</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {calculations.calculations.map((item, index) => {
                      const isSelected = selectedItems.some(i => i.article === item.article && i.depot === item.depot && i.packaging === item.packaging);
                      return (
                        <tr key={index} className={`hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleItemSelection(item)}
                              className="rounded"
                            />
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.article}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.depot}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${
                              item.packaging === 'verre' ? 'bg-blue-100 text-blue-800' :
                              item.packaging === 'pet' ? 'bg-green-100 text-green-800' :
                              item.packaging === 'ciel' ? 'bg-purple-100 text-purple-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {item.packaging}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.cqm}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.stock_actuel}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.stock_transit}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.quantite_a_envoyer}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {item.palettes_needed || 0}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.stock_dispo_m210}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              item.is_locally_made 
                                ? 'bg-slate-100 text-slate-800 border border-slate-200' 
                                : 'bg-amber-100 text-amber-800 border border-amber-200'
                            }`}>
                              {item.sourcing_text || (item.is_locally_made ? 'Production Locale' : 'Sourcing Externe')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {getStatusIcon(item.statut)}
                              <span className={`ml-2 text-sm font-medium ${
                                item.statut === 'OK' ? 'text-green-600' :
                                item.statut === 'À livrer' ? 'text-orange-600' : 'text-red-600'
                              }`}>
                                {item.statut}
                              </span>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;