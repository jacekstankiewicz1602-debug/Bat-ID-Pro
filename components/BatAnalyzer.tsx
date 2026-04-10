"use client";

import { useState } from "react";
import { Upload, FileAudio, Loader2, CheckCircle2, AlertCircle, BarChart2 } from "lucide-react";
import { Button } from "@/components/ui/neon-button";
import { motion, AnimatePresence } from "framer-motion";

interface AnalysisResult {
  timestamp: string;
  species: string;
  confidence: number;
}

export default function BatAnalyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResults(null);
    }
  };

  const analyzeAudio = async () => {
    if (!file) return;

    setIsAnalyzing(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data.results);
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

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-8">
      <div className="text-center space-y-4">
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Bat Sound Identification
        </h2>
        <p className="text-lg text-zinc-400">
          Upload a high-frequency audio recording to identify bat species.
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Upload Area */}
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
              <p className="text-base font-medium text-white">
                {file ? file.name : "Click or drag to upload"}
              </p>
              <p className="text-sm text-zinc-500">
                WAV, MP3, OGG up to 10MB
              </p>
            </div>
          </div>
        </div>

        {/* Controls and Status */}
        <div className="flex flex-col justify-center space-y-6">
          <Button
            size="lg"
            className="w-full h-16 text-lg font-semibold"
            disabled={!file || isAnalyzing}
            onClick={analyzeAudio}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Analyzing Audio...
              </>
            ) : (
              "Identify Species"
            )}
          </Button>

          <AnimatePresence mode="wait">
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center gap-3 rounded-2xl bg-red-500/10 p-4 text-red-400 border border-red-500/20"
              >
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <p className="text-sm font-medium">{error}</p>
              </motion.div>
            )}

            {results && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-3 rounded-2xl bg-emerald-500/10 p-4 text-emerald-400 border border-emerald-500/20"
              >
                <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
                <p className="text-sm font-medium">Analysis complete. Found {results.length} detection segments.</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Results Section */}
      <AnimatePresence>
        {results && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="overflow-hidden space-y-6 pt-8"
          >
            <div className="flex items-center gap-2 text-white">
              <BarChart2 className="h-5 w-5 text-blue-400" />
              <h3 className="text-xl font-semibold">Classification Results</h3>
            </div>

            <div className="overflow-x-auto rounded-3xl border border-zinc-800 bg-zinc-950/50 backdrop-blur-xl">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-zinc-800 bg-zinc-900/50">
                    <th className="px-6 py-4 text-sm font-semibold text-zinc-400">Segment (s)</th>
                    <th className="px-6 py-4 text-sm font-semibold text-zinc-400">Identified Species</th>
                    <th className="px-6 py-4 text-sm font-semibold text-zinc-400">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {results.map((result, idx) => (
                    <motion.tr 
                      key={idx}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="transition-colors hover:bg-zinc-900/50"
                    >
                      <td className="px-6 py-4 text-sm font-medium text-zinc-300">{result.timestamp}</td>
                      <td className="px-6 py-4 text-sm font-semibold text-white">{result.species}</td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-24 rounded-full bg-zinc-800 overflow-hidden">
                            <motion.div 
                              initial={{ width: 0 }}
                              animate={{ width: `${result.confidence * 100}%` }}
                              className={`h-full ${
                                result.confidence > 0.8 ? "bg-emerald-500" : 
                                result.confidence > 0.6 ? "bg-yellow-500" : "bg-red-500"
                              }`}
                            />
                          </div>
                          <span className="text-xs font-medium text-zinc-400">
                            {(result.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
