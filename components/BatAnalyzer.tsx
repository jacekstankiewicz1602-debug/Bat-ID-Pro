"use client";

import { useState, useRef } from "react";
import { 
  Upload, 
  FileAudio, 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  BarChart2, 
  Settings2, 
  Download,
  Image as ImageIcon
} from "lucide-react";
import { Button } from "@/components/ui/neon-button";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface AnalysisResult {
  timestamp: string;
  species: string;
  confidence: number;
}

const MODELS = [
  { id: "BattyBirdNET-EU-256kHz", name: "Europe (General)" },
  { id: "BattyBirdNET-UK-256kHz", name: "United Kingdom" },
  { id: "BattyBirdNET-USA-256kHz", name: "USA (General)" },
  { id: "BattyBirdNET-Bavaria-256kHz-high", name: "Bavaria (High Sens)" },
  { id: "BattyBirdNET-Scotland-256kHz", name: "Scotland" },
  { id: "BattyBirdNET-Sweden-256kHz", name: "Sweden" },
];

export default function BatAnalyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResult[] | null>(null);
  const [spectrogram, setSpectrogram] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Settings
  const [minConfidence, setMinConfidence] = useState(0.5);
  const [selectedModel, setSelectedModel] = useState(MODELS[0].id);
  const [showSettings, setShowSettings] = useState(true); // Default to open for visibility

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResults(null);
      setSpectrogram(null);
    }
  };

  const analyzeAudio = async () => {
    if (!file) return;

    setIsAnalyzing(true);
    setError(null);
    setResults(null);
    setSpectrogram(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("min_confidence", minConfidence.toString());
    formData.append("model", selectedModel);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data.results);
        setSpectrogram(data.spectrogram);
      } else {
        setError(data.error || "Failed to analyze audio.");
      }
    } catch (err) {
      setError("An error occurred during analysis. Please try again.");
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadCSV = () => {
    if (!results) return;

    const headers = "Timestamp,Species,Confidence\n";
    const csvContent = results.map(r => `${r.timestamp},${r.species},${(r.confidence * 100).toFixed(2)}%`).join("\n");
    const blob = new Blob([headers + csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bat_analysis_${file?.name || "result"}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full max-w-5xl mx-auto p-6 space-y-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Bat Sound Identification
          </h2>
          <p className="text-lg text-zinc-400">
            Professional bat vocalization analysis and visualization.
          </p>
        </div>
        <Button 
          variant="ghost" 
          onClick={() => setShowSettings(!showSettings)}
          className={cn(
            "border-zinc-800 text-zinc-400 hover:text-white transition-colors px-4 py-2",
            showSettings && "bg-blue-500/10 border-blue-500/50 text-blue-400"
          )}
        >
          <Settings2 className="mr-2 h-4 w-4" />
          {showSettings ? "Hide Settings" : "Show Settings"}
        </Button>
      </div>

      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="grid gap-6 md:grid-cols-2 p-6 rounded-3xl border border-zinc-800 bg-zinc-950/50 backdrop-blur-sm">
              <div className="space-y-3">
                <label className="text-sm font-medium text-zinc-400 flex justify-between">
                  Confidence Threshold <span>{Math.round(minConfidence * 100)}%</span>
                </label>
                <input 
                  type="range" 
                  min="0.1" 
                  max="0.95" 
                  step="0.05" 
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                  className="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <p className="text-xs text-zinc-500 italic">Only detections above this certainty will be shown.</p>
              </div>
              <div className="space-y-3">
                <label className="text-sm font-medium text-zinc-400">Regional Model</label>
                <select 
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {MODELS.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                </select>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid gap-8 lg:grid-cols-12">
        <div className="lg:col-span-5 space-y-6">
          <div 
            className="relative group rounded-3xl border-2 border-dashed border-zinc-800 bg-zinc-900/50 p-12 transition-all hover:border-zinc-700 hover:bg-zinc-900"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                setFile(e.dataTransfer.files[0]);
              }
            }}
          >
            <input
              type="file"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleFileChange}
              accept=".wav,.mp3,.ogg,.flac"
            />
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="rounded-full bg-zinc-800 p-4 transition-transform group-hover:scale-110">
                {file ? (
                  <FileAudio className="h-8 w-8 text-blue-400" />
                ) : (
                  <Upload className="h-8 w-8 text-zinc-400" />
                )}
              </div>
              <div className="space-y-2">
                <p className="text-base font-medium text-white max-w-[200px] truncate">
                  {file ? file.name : "Click or drag to upload"}
                </p>
                <p className="text-sm text-zinc-500 uppercase tracking-wider">
                  Audio Analysis
                </p>
              </div>
            </div>
          </div>

          <Button
            size="lg"
            className="w-full h-16 text-lg font-semibold shadow-2xl shadow-blue-500/20"
            disabled={!file || isAnalyzing}
            onClick={analyzeAudio}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Processing...
              </>
            ) : (
              "Identify Bat Species"
            )}
          </Button>

          <AnimatePresence mode="wait">
            {error && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-3 rounded-2xl bg-red-500/10 p-4 text-red-400 border border-red-500/20"
              >
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <p className="text-sm font-medium">{error}</p>
              </motion.div>
            )}
            {results && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center justify-between gap-3 rounded-2xl bg-emerald-500/10 p-4 text-emerald-400 border border-emerald-500/20"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
                  <p className="text-sm font-medium">Found {results.length} detection(s)</p>
                </div>
                <Button variant="ghost" size="sm" onClick={downloadCSV} className="h-8 text-emerald-400 hover:bg-emerald-500/20">
                  <Download className="mr-2 h-3.5 w-3.5" />
                  CSV
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="lg:col-span-7 space-y-8">
           {/* Spectrogram View */}
           <div className="rounded-3xl border border-zinc-800 bg-zinc-950 overflow-hidden relative min-h-[240px] flex items-center justify-center">
              {spectrogram ? (
                <div className="w-full h-full p-2">
                   <div className="flex items-center gap-2 mb-2 px-4 pt-2">
                      <ImageIcon className="h-4 w-4 text-blue-400" />
                      <span className="text-xs font-semibold text-zinc-500 uppercase tracking-tighter">Voice Spectrogram</span>
                   </div>
                   <img 
                    src={`data:image/png;base64,${spectrogram}`} 
                    alt="Spectrogram" 
                    className="w-full h-[200px] object-cover rounded-xl"
                  />
                </div>
              ) : (
                <div className="text-center space-y-2 opacity-20">
                  <BarChart2 className="h-12 w-12 mx-auto text-zinc-600" />
                  <p className="text-sm text-zinc-500">Visualization will appear here</p>
                </div>
              )}
           </div>

           {/* Results Table */}
           {results && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="overflow-x-auto rounded-3xl border border-zinc-800 bg-zinc-950/30 backdrop-blur-xl"
              >
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-zinc-800 bg-zinc-900/20">
                      <th className="px-6 py-4 text-xs font-bold text-zinc-500 uppercase">Segment</th>
                      <th className="px-6 py-4 text-xs font-bold text-zinc-500 uppercase">Species</th>
                      <th className="px-6 py-4 text-xs font-bold text-zinc-500 uppercase text-right">Match</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900">
                    {results.length > 0 ? results.map((result, idx) => (
                      <motion.tr 
                        key={idx}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: idx * 0.05 }}
                        className="transition-colors hover:bg-zinc-800/30"
                      >
                        <td className="px-6 py-4 text-sm font-mono text-zinc-400">{result.timestamp}s</td>
                        <td className="px-6 py-4 text-sm font-bold text-white leading-tight">
                           {result.species.split("_").slice(-1)}
                           <div className="text-[10px] font-medium text-zinc-500">{result.species}</div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <span className={`px-2 py-1 rounded-md text-[10px] font-black ${
                            result.confidence > 0.8 ? "bg-emerald-500/20 text-emerald-400" : 
                            result.confidence > 0.6 ? "bg-yellow-500/20 text-yellow-400" : "bg-red-500/20 text-red-500"
                          }`}>
                            {(result.confidence * 100).toFixed(0)}%
                          </span>
                        </td>
                      </motion.tr>
                    )) : (
                      <tr>
                        <td colSpan={3} className="px-6 py-12 text-center text-zinc-600 italic">No significant detections found with current threshold.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </motion.div>
           )}
        </div>
      </div>

      <footer className="pt-8 text-center border-t border-zinc-900">
        <p className="text-zinc-600 text-[10px] uppercase tracking-widest font-bold">
          Bioacoustic Analysis System • v1.2 Build 2026
        </p>
      </footer>
    </div>
  );
}
