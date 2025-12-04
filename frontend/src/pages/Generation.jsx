import React, { useState, useEffect, useRef } from 'react';
import { Zap, Settings, Play, RotateCcw, Plus, Trash2, Code, FileText, AlertTriangle, CheckCircle, Loader, Clock, X, Database, Search, ShieldCheck } from 'lucide-react';
import { generateResearch, generateInjection, generateValidation, getSample } from '../api';

const Generation = () => {
  const [funcCode, setFuncCode] = useState('');
  const [funcName, setFuncName] = useState('');
  const [cweIds, setCweIds] = useState('');
  const [rois, setRois] = useState([{ roi: '', line: '' }]);
  const [errors, setErrors] = useState({});
  const [skipValidation, setSkipValidation] = useState(false);
  
  const lineNumbersRef = useRef(null);

  // Generation State
  const [generationStep, setGenerationStep] = useState(0); // 0: Idle, 1-4: Steps, 5: Finished
  const [showModal, setShowModal] = useState(false);
  const [errorModal, setErrorModal] = useState(null); // { message: string }

  const steps = [
    { id: 1, label: 'Researching CWE', icon: Search },
    { id: 2, label: 'Checking Condensed Knowledge', icon: Database },
    { id: 3, label: 'Performing Injection', icon: Zap },
    { id: 4, label: 'Validating Injection', icon: ShieldCheck },
  ];

  const handleAddRoi = () => {
    setRois([...rois, { roi: '', line: '' }]);
  };

  const handleRemoveRoi = (index) => {
    const newRois = rois.filter((_, i) => i !== index);
    setRois(newRois);
  };

  const handleRoiChange = (index, field, value) => {
    const newRois = [...rois];
    newRois[index][field] = value;
    setRois(newRois);
  };

  const validateInput = () => {
    const newErrors = {};
    
    // 1. Func Code: No empty code
    if (!funcCode || funcCode.trim() === '') {
      newErrors.funcCode = 'Function code is required.';
    }

    // 2. Func Name: No empty name
    if (!funcName || funcName.trim() === '') {
      newErrors.funcName = 'Function name is required.';
    }

    // 3. CWE IDs: Required and Comma separated
    if (!cweIds || cweIds.trim() === '') {
      newErrors.cweIds = 'CWE IDs are required.';
    } else if (!/^[\w-]+(,\s*[\w-]+)*$/.test(cweIds.trim())) {
      newErrors.cweIds = 'CWE IDs must be comma-separated (e.g., CWE-78, CWE-89).';
    }

    // 4. ROIs: At least 1 ROI
    if (rois.length === 0) {
      newErrors.rois = 'At least one Region of Interest (ROI) is required.';
    } else {
      rois.forEach((item, index) => {
        // ROI Code: Not empty
        if (!item.roi || item.roi.trim() === '') {
          newErrors[`roi_${index}`] = 'ROI code is required.';
        }
        
        // Line: Number or Range (e.g., "1" or "6-8")
        if (!item.line || !/^(\d+|(\d+-\d+))$/.test(item.line.trim())) {
          newErrors[`line_${index}`] = 'Invalid line format (e.g., 1 or 6-8).';
        }
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleGenerate = async () => {
    if (!validateInput()) return;

    setGenerationStep(1);
    
    try {
        // 1. Research Step
        const cweList = cweIds.split(',').map(id => id.trim()).filter(id => id);
        for (const cweId of cweList) {
             const res = await generateResearch({ cwe_id: cweId });
             if (!res.data) throw new Error(`Research failed for ${cweId}`);
        }

        // 2. Injection Step (Visualized as Step 2 & 3)
        setGenerationStep(2);
        
        // Format Inputs
        const roiStr = rois.map((r, i) => `${i + 1}. ${r.roi}`).join('\n');
        const lineStr = rois.map(r => r.line).join('\n');

        const injectionRes = await generateInjection({
            func_name: funcName,
            func_code: funcCode,
            lines: lineStr,
            rois: roiStr,
            cwe_ids: cweIds
        });
        
        if (!injectionRes.data) throw new Error("Injection failed");
        
        setGenerationStep(3); // Move to "Performing Injection" visually if needed, or just jump to 4

        // 3. Validation Step
        if (!skipValidation) {
            setGenerationStep(4);
            const validationRes = await generateValidation({
                func_name: funcName,
                func_code: funcCode,
                merged_roi_lines: lineStr
            });
            if (!validationRes.data) throw new Error("Validation failed");
        }

        setGenerationStep(5);
        setShowModal(true);

    } catch (error) {
        console.error("Generation Error:", error);
        setErrorModal({ message: error.message || "An unexpected error occurred." });
        setGenerationStep(0);
    }
  };

  const handleReset = () => {
    setFuncCode('');
    setFuncName('');
    setCweIds('');
    setRois([{ roi: '', line: '' }]);
    setErrors({});
    setGenerationStep(0);
    setShowModal(false);
    setErrorModal(null);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 h-[calc(100vh-100px)] flex flex-col relative">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
            <h1 className="text-3xl font-bold text-white mb-1">New Generation</h1>
            <p className="text-gray-400 text-sm">Configure injection parameters and target code.</p>
        </div>
        <div className="flex gap-3">
            <button 
                className="flex items-center text-gray-400 hover:text-white transition-colors text-sm font-medium px-3 py-2"
                onClick={handleReset}
                disabled={generationStep > 0 && generationStep < 5}
            >
                <RotateCcw size={16} className="mr-2" /> Reset
            </button>
            <button 
                className="flex items-center text-blue-400 hover:text-blue-300 transition-colors text-sm font-medium px-3 py-2 border border-blue-500/30 rounded-lg bg-blue-500/10"
                onClick={async () => {
                    try {
                        const res = await getSample();
                        if (res.data) {
                            setFuncName(res.data.func_name);
                            setFuncCode(res.data.raw_code);
                            setCweIds(res.data.cwe_ids);
                            
                            // Parse ROIs and Lines
                            const rawRoi = res.data.roi || '';
                            const rawLines = res.data.merged_roi_lines ? String(res.data.merged_roi_lines) : '';
                            
                            // Split lines by newline (assuming they are newline separated based on inspection)
                            // If it's a single block of digits, we might need a fallback, but let's try newline first.
                            let lines = rawLines.split(/\r?\n/).map(l => l.trim()).filter(l => l);
                            
                            // Parse ROIs: Split by "N. " pattern
                            // Regex looks for digit + dot + space
                            const roiParts = rawRoi.split(/(\d+)\.\s/);
                            // Result will be ["", "1", "code...", "2", "code...", ...]
                            
                            const parsedRois = [];
                            for (let i = 1; i < roiParts.length; i += 2) {
                                const index = roiParts[i];
                                const code = roiParts[i+1];
                                if (code) {
                                    parsedRois.push({
                                        roi: code.trim(),
                                        line: lines[parsedRois.length] || '' // Map to corresponding line
                                    });
                                }
                            }
                            
                            // Fallback if parsing failed or empty
                            if (parsedRois.length === 0) {
                                parsedRois.push({ roi: rawRoi, line: rawLines });
                            }
                            
                            setRois(parsedRois);
                        }
                    } catch (e) {
                        console.error("Failed to load sample:", e);
                        setErrorModal({ message: "Failed to load sample data." });
                    }
                }}
                disabled={generationStep > 0}
            >
                <FileText size={16} className="mr-2" /> Sample
            </button>
            <button 
                onClick={handleGenerate}
                disabled={generationStep > 0}
                className={`flex items-center px-6 py-2 rounded-lg font-medium transition-all ${
                    generationStep > 0
                    ? 'bg-blue-600/50 text-blue-200 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20'
                }`}
            >
                {generationStep > 0 && generationStep < 5 ? (
                    <>
                        <Loader size={18} className="animate-spin mr-2" /> Processing...
                    </>
                ) : (
                    <>
                        <Zap size={18} className="mr-2" /> Generate
                    </>
                )}
            </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        
        {/* Left Column: Code Editor */}
        <div className={`bg-gray-800 rounded-xl border flex flex-col overflow-hidden shadow-xl transition-colors ${errors.funcCode ? 'border-red-500' : 'border-gray-700'}`}>
            <div className="bg-gray-900/50 px-4 py-3 border-b border-gray-700 flex items-center justify-between text-gray-300 font-medium">
                <div className="flex items-center gap-2">
                    <Code size={18} className="text-blue-400" />
                    <span>Function Code</span>
                </div>
                {errors.funcCode && <span className="text-red-400 text-xs">{errors.funcCode}</span>}
            </div>
            <div className="flex-1 relative flex overflow-hidden">
                <div 
                    ref={lineNumbersRef}
                    className="bg-gray-900/30 text-gray-600 font-mono text-sm py-4 pr-3 pl-2 text-right select-none border-r border-gray-800 overflow-hidden"
                    style={{ lineHeight: '1.5rem', minWidth: '3rem' }}
                >
                    {funcCode.split('\n').map((_, i) => (
                        <div key={i}>{i + 1}</div>
                    ))}
                </div>
                <textarea 
                    value={funcCode}
                    onChange={(e) => setFuncCode(e.target.value)}
                    onScroll={(e) => {
                        if (lineNumbersRef.current) {
                            lineNumbersRef.current.scrollTop = e.target.scrollTop;
                        }
                    }}
                    placeholder="// Paste your target function code here..."
                    className="flex-1 w-full bg-gray-900/50 p-4 text-gray-300 font-mono text-sm focus:outline-none resize-none whitespace-pre leading-6"
                    style={{ lineHeight: '1.5rem' }}
                    spellCheck="false"
                    disabled={generationStep > 0}
                />
            </div>
        </div>

        {/* Right Column: Configuration OR Timeline */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 flex flex-col overflow-hidden shadow-xl transition-all duration-300">
            {generationStep === 0 ? (
                // CONFIGURATION VIEW
                <>
                    <div className="bg-gray-900/50 px-4 py-3 border-b border-gray-700 flex items-center gap-2 text-gray-300 font-medium">
                        <Settings size={18} className="text-purple-400" />
                        <span>Configuration</span>
                    </div>
                    
                    <div className="p-6 space-y-6 overflow-y-auto flex-1">
                        {/* Metadata Section */}
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <label className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                                        <FileText size={14} /> Function Name
                                    </label>
                                    {errors.funcName && <span className="text-red-400 text-xs">{errors.funcName}</span>}
                                </div>
                                <input 
                                    type="text" 
                                    value={funcName}
                                    onChange={(e) => setFuncName(e.target.value)}
                                    placeholder="e.g., process_user_data"
                                    className={`w-full bg-gray-900 border rounded-lg p-2.5 text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${errors.funcName ? 'border-red-500' : 'border-gray-700'}`}
                                />
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <label className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                                        <AlertTriangle size={14} /> CWE IDs
                                    </label>
                                    {errors.cweIds && <span className="text-red-400 text-xs">{errors.cweIds}</span>}
                                </div>
                                <input 
                                    type="text" 
                                    value={cweIds}
                                    onChange={(e) => setCweIds(e.target.value)}
                                    placeholder="e.g., CWE-78, CWE-89"
                                    className={`w-full bg-gray-900 border rounded-lg p-2.5 text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${errors.cweIds ? 'border-red-500' : 'border-gray-700'}`}
                                />
                            </div>
                        </div>

                        <div className="border-t border-gray-700 my-4"></div>

                        {/* ROI Section */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                                    Regions of Interest (ROIs)
                                </label>
                                <button 
                                    onClick={handleAddRoi}
                                    className="text-xs flex items-center gap-1 text-blue-400 hover:text-blue-300 font-medium transition-colors"
                                >
                                    <Plus size={14} /> Add Region
                                </button>
                            </div>
                            {errors.rois && <div className="text-red-400 text-xs">{errors.rois}</div>}

                            <div className="space-y-3">
                                {rois.map((item, index) => (
                                    <div key={index} className="flex gap-3 items-start animate-fadeIn relative">
                                        <div className="flex-1 space-y-1">
                                            <input 
                                                type="text" 
                                                value={item.roi}
                                                onChange={(e) => handleRoiChange(index, 'roi', e.target.value)}
                                                placeholder="ROI Code"
                                                className={`w-full bg-gray-900 border rounded-lg p-2 text-sm text-gray-200 focus:ring-1 focus:ring-blue-500 focus:border-transparent ${errors[`roi_${index}`] ? 'border-red-500' : 'border-gray-700'}`}
                                            />
                                        </div>
                                        <div className="w-24 space-y-1 relative group">
                                            <input 
                                                type="text" 
                                                value={item.line}
                                                onChange={(e) => handleRoiChange(index, 'line', e.target.value)}
                                                placeholder="Line #"
                                                className={`w-full bg-gray-900 border rounded-lg p-2 text-sm text-gray-200 focus:ring-1 focus:ring-blue-500 focus:border-transparent text-center ${errors[`line_${index}`] ? 'border-red-500' : 'border-gray-700'}`}
                                            />
                                            {errors[`line_${index}`] && (
                                                <div className="absolute right-0 top-full mt-1 w-48 p-2 bg-red-900/90 border border-red-500 rounded text-xs text-red-200 z-10 shadow-xl backdrop-blur-sm">
                                                    {errors[`line_${index}`]}
                                                </div>
                                            )}
                                        </div>
                                        <button 
                                            onClick={() => handleRemoveRoi(index)}
                                            className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors mt-0.5"
                                            title="Remove ROI"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="border-t border-gray-700 my-4"></div>

                        {/* Options */}
                        <div className="flex items-center gap-2">
                             <input 
                                type="checkbox" 
                                id="skipValidation"
                                checked={skipValidation}
                                onChange={(e) => setSkipValidation(e.target.checked)}
                                className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900"
                             />
                             <label htmlFor="skipValidation" className="text-sm text-gray-300 cursor-pointer select-none">
                                Skip Validation Step
                             </label>
                        </div>
                    </div>
                </>
            ) : (
                // TIMELINE VIEW
                <div className="flex flex-col h-full">
                    <div className="bg-gray-900/50 px-4 py-3 border-b border-gray-700 flex items-center gap-2 text-gray-300 font-medium">
                        <Clock size={18} className="text-blue-400" />
                        <span>Generation Progress</span>
                    </div>
                    <div className="p-8 flex-1 flex flex-col justify-center items-center">
                        <div className="space-y-8 relative min-w-[320px]">
                            {/* Vertical Line - Perfectly centered through icons */}
                            <div className="absolute left-6 top-4 bottom-4 w-0.5 bg-gray-700 -z-10 -translate-x-1/2"></div>

                            {steps.map((step) => {
                                const isCompleted = generationStep > step.id || generationStep === 5;
                                const isCurrent = generationStep === step.id;
                                const isPending = generationStep < step.id;
                                
                                // Skip Validation step if selected
                                if (step.id === 4 && skipValidation) return null;

                                return (
                                    <div key={step.id} className={`flex items-center gap-4 transition-all duration-500 ${isPending ? 'opacity-40' : 'opacity-100'}`}>
                                        <div className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-500 z-10 bg-gray-800 shrink-0 ${
                                            isCompleted ? 'border-green-500 text-green-500' :
                                            isCurrent ? 'border-blue-500 text-blue-500 shadow-lg shadow-blue-500/20' :
                                            'border-gray-600 text-gray-600'
                                        }`}>
                                            {isCompleted ? <CheckCircle size={24} /> :
                                             isCurrent ? <step.icon size={24} className="animate-pulse" /> :
                                             <step.icon size={24} />}
                                        </div>
                                        <div>
                                            <h3 className={`text-lg font-medium leading-none mb-1 transition-colors ${
                                                isCompleted ? 'text-green-400' :
                                                isCurrent ? 'text-blue-400' :
                                                'text-gray-500'
                                            }`}>
                                                {step.label}
                                            </h3>
                                            {isCurrent && <p className="text-sm text-gray-400 animate-pulse leading-none">Processing...</p>}
                                            {isCompleted && <p className="text-sm text-gray-500 leading-none">Completed</p>}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            )}
        </div>
      </div>

      {/* Result Modal */}
      {showModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm animate-fadeIn">
            <div className="bg-gray-800 border border-gray-700 rounded-2xl shadow-2xl w-full max-w-md p-6 transform transition-all scale-100">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-green-500/20 rounded-full text-green-400">
                            <CheckCircle size={24} />
                        </div>
                        <h2 className="text-xl font-bold text-white">Generation Complete</h2>
                    </div>
                    <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white">
                        <X size={24} />
                    </button>
                </div>
                
                <div className="space-y-4 mb-6">
                    <p className="text-gray-300">
                        All artifacts have been successfully generated and saved to your collection.
                    </p>
                    
                    <div className="bg-gray-900/50 rounded-lg p-4 space-y-3 border border-gray-700">
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-500">Function Name</span>
                            <span className="text-gray-200 font-medium">{funcName}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-500">CWE IDs</span>
                            <span className="text-gray-200">{cweIds}</span>
                        </div>
                    </div>
                </div>

                <div className="flex gap-3">
                    <button 
                        onClick={handleReset}
                        className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
                    >
                        Start New
                    </button>
                    <button 
                        onClick={() => {
                            window.location.href = `/injections/group/${funcName}`;
                        }}
                        className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
                    >
                        View Results
                    </button>
                </div>
            </div>
        </div>
      )}

      {/* Error Modal */}
      {errorModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm animate-fadeIn">
            <div className="bg-gray-800 border border-red-500/50 rounded-2xl shadow-2xl w-full max-w-md p-6 transform transition-all scale-100">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-red-500/20 rounded-full text-red-400">
                            <AlertTriangle size={24} />
                        </div>
                        <h2 className="text-xl font-bold text-white">Generation Failed</h2>
                    </div>
                    <button onClick={() => setErrorModal(null)} className="text-gray-400 hover:text-white">
                        <X size={24} />
                    </button>
                </div>
                
                <div className="mb-6">
                    <p className="text-gray-300 mb-2">An error occurred during the generation process:</p>
                    <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 text-red-200 text-sm font-mono break-words">
                        {errorModal.message}
                    </div>
                </div>

                <div className="flex gap-3">
                    <button 
                        onClick={handleReset}
                        className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
                    >
                        Reset
                    </button>
                    <button 
                        onClick={() => {
                            setErrorModal(null);
                            handleGenerate(); // Retry
                        }}
                        className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
};

export default Generation;
