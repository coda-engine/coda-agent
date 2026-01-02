import { useState, useEffect } from 'react'
import { Bot, Send, Settings, History, Plus, MessageSquare, Trash2, GitBranch, BarChart2, Paperclip, X, FileText, Share2, Download, ThumbsUp, ThumbsDown, Key } from 'lucide-react'
import { submitFeedback } from './api/feedback'
import { uploadFile } from './api/files'
import { useRef } from 'react'
import Analytics from './pages/Analytics'

interface Session {
    id: string
    title: string
    created_at: string
}

function App() {
    const [input, setInput] = useState('')
    const [attachments, setAttachments] = useState<{ filename: string; content: string }[]>([])
    const [messages, setMessages] = useState<any[]>([
        { role: 'assistant', content: 'Hello! I am Coda Agent. How can I help you today?' }
    ])
    const [sessions, setSessions] = useState<Session[]>([])
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
    const [health, setHealth] = useState<any>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [showSettings, setShowSettings] = useState(false)
    const [apiKeys, setApiKeys] = useState({
        openai: localStorage.getItem('openai_api_key') || '',
        anthropic: localStorage.getItem('anthropic_api_key') || '',
        google: localStorage.getItem('google_api_key') || ''
    })
    const [selectedModel, setSelectedModel] = useState(localStorage.getItem('selected_model') || 'gpt-4')

    // Temp state for modal
    const [tempKeys, setTempKeys] = useState(apiKeys)
    const [tempModel, setTempModel] = useState(selectedModel)

    useEffect(() => {
        setTempKeys(apiKeys)
        setTempModel(selectedModel)
    }, [apiKeys, selectedModel, showSettings])

    const handleSaveSettings = () => {
        setApiKeys(tempKeys)
        setSelectedModel(tempModel)
        localStorage.setItem('openai_api_key', tempKeys.openai)
        localStorage.setItem('anthropic_api_key', tempKeys.anthropic)
        localStorage.setItem('google_api_key', tempKeys.google)
        localStorage.setItem('selected_model', tempModel)
        setShowSettings(false)
    }

    const [view, setView] = useState<'chat' | 'analytics'>('chat')
    const fileInputRef = useRef<HTMLInputElement>(null)

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            const result = await uploadFile(file);
            setAttachments(prev => [...prev, { filename: result.filename, content: result.content }]);
        } catch (error) {
            console.error("Upload failed", error);
            const msg = error instanceof Error ? error.message : String(error);
            alert("Upload failed: " + msg);
        } finally {
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const removeAttachment = (index: number) => {
        setAttachments(prev => prev.filter((_, i) => i !== index));
    };


    useEffect(() => {
        checkHealth()
        fetchSessions()

        // Check URL for session
        const params = new URLSearchParams(window.location.search);
        const urlSessionId = params.get('session');
        if (urlSessionId) {
            loadSession(urlSessionId);
        }
    }, [])

    // Sync URL with session state
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        if (currentSessionId) {
            if (params.get('session') !== currentSessionId) {
                params.set('session', currentSessionId);
                window.history.pushState({}, '', `${window.location.pathname}?${params}`);
            }
        } else {
            if (params.has('session')) {
                params.delete('session');
                window.history.pushState({}, '', window.location.pathname);
            }
        }
    }, [currentSessionId])

    const checkHealth = () => {
        fetch(`${import.meta.env.VITE_API_URL}/health`)
            .then(res => res.json())
            .then(data => setHealth(data))
            .catch(err => console.error('Backend health check failed', err))
    }

    const fetchSessions = async () => {
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/sessions/`)
            if (res.ok) {
                const data = await res.json()
                setSessions(data)
            }
        } catch (error) {
            console.error('Failed to fetch sessions', error)
        }
    }

    const loadSession = async (sessionId: string) => {
        setIsLoading(true)
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/sessions/${sessionId}`)
            if (res.ok) {
                const data = await res.json()
                setCurrentSessionId(data.id)
                const uiMessages: any[] = []

                data.messages.forEach((m: any) => {
                    if (m.role === 'user') {
                        // Extract attachments from content
                        const fileRegex = /\[Attached File: (.*?)\]\n([\s\S]*?)\n\[End Attachment\]/g;
                        let content = m.content || '';
                        const attachments = [];
                        let match;

                        // Reset regex
                        fileRegex.lastIndex = 0;

                        // We need to loop manually to strip correctly
                        // Or just use split/replace logic
                        const files = []
                        let cleanContent = content

                        while ((match = fileRegex.exec(content)) !== null) {
                            files.push({ filename: match[1], content: match[2].trim() });
                        }

                        if (files.length > 0) {
                            cleanContent = content.replace(fileRegex, '').trim();
                        }

                        uiMessages.push({
                            id: m.id,
                            role: m.role,
                            content: cleanContent,
                            attachments: files,
                            tokenUsage: m.token_count
                        });

                    } else if (m.role === 'tool') {
                        // Hide raw tool outputs from main stream
                        // Optionally attach result to previous assistant message if needed for "Result" display
                        // For now, hiding avoids the "raw text" issue
                    } else {
                        uiMessages.push({
                            id: m.id,
                            role: m.role,
                            content: m.content || '',
                            tokenUsage: m.token_count,
                            executionTime: m.execution_time,
                            decisionCount: m.decision_count,
                            tool_calls: m.tool_calls,
                            thoughts: m.feedback?.thoughts || m.thoughts,
                            feedback: m.feedback
                        })
                    }
                })

                setMessages(uiMessages)
            }
        } catch (error) {
            console.error('Failed to load session', error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleFork = async (messageId: string) => {
        if (!currentSessionId) return

        // Optimistic UI? No, wait for result.
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/sessions/${currentSessionId}/fork`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message_id: messageId })
            })
            if (!res.ok) throw new Error('Fork failed')

            const newSession = await res.json()
            await fetchSessions()
            loadSession(newSession.id)

        } catch (err) {
            console.error(err)
            alert('Failed to branch conversation')
        }
    }

    const deleteSession = async (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation()
        if (!confirm('Delete this chat?')) return
        try {
            await fetch(`${import.meta.env.VITE_API_URL}/api/v1/sessions/${sessionId}`, {
                method: 'DELETE'
            })
            setSessions(prev => prev.filter(s => s.id !== sessionId))
            if (currentSessionId === sessionId) {
                handleNewChat()
            }
        } catch (error) {
            console.error('Failed to delete session', error)
        }
    }

    const handleNewChat = () => {
        setCurrentSessionId(null)
        setMessages([{ role: 'assistant', content: 'Hello! I am Coda Agent. How can I help you today?' }])
        setView('chat')
    }

    const handleShare = async () => {
        if (!currentSessionId) {
            alert("Start a chat to share.");
            return;
        }

        const url = `${window.location.origin}${window.location.pathname}?session=${currentSessionId}`;

        try {
            await navigator.clipboard.writeText(url);
            alert("Link copied to clipboard: " + url);
        } catch (err) {
            console.error("Clipboard write failed", err);
            // Fallback for non-secure contexts or permission errors
            prompt("Copy this link to share:", url);
        }
    }

    const handleExport = () => {
        if (!messages.length) return;
        const exportData = {
            meta: {
                session_id: currentSessionId,
                title: sessions.find(s => s.id === currentSessionId)?.title,
                exported_at: new Date().toISOString(),
                application: "Coda Agent"
            },
            messages: messages
        };
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `coda-chat-${currentSessionId || 'new'}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    const handleFeedback = async (msgId: string, score: number, index: number) => {
        if (!msgId) return;
        try {
            console.log("Submitting feedback for:", msgId);
            console.log("API URL:", import.meta.env.VITE_API_URL);
            await submitFeedback(msgId, score);
            setMessages(prev => {
                const newMessages = [...prev];
                if (newMessages[index]) {
                    newMessages[index] = { ...newMessages[index], feedback: { score } };
                }
                return newMessages;
            });
        } catch (error) {
            console.error("Feedback failed", error);
            const msg = error instanceof Error ? error.message : String(error);
            alert(msg);
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() && attachments.length === 0) return

        // Create UI message (clean)
        const uiMsg = {
            role: 'user',
            content: input,
            attachments: [...attachments] // copy 
        }
        setMessages(prev => [...prev, uiMsg])

        // Prepare Server message (with file content hidden in text)
        let serverContent = input;
        if (attachments.length > 0) {
            const attachmentsStr = attachments.map(a => `\n\n[Attached File: ${a.filename}]\n${a.content}\n[End Attachment]`).join('');
            serverContent += attachmentsStr;
        }

        setInput('')
        setAttachments([])

        // Add empty assistant message to start
        setMessages(prev => [...prev, { role: 'assistant', content: '' }])

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-OpenAI-API-Key': apiKeys.openai,
                    'X-Anthropic-API-Key': apiKeys.anthropic,
                    'X-Google-API-Key': apiKeys.google,
                },
                body: JSON.stringify({
                    session_id: currentSessionId, // Pass current session
                    messages: [{ role: 'user', content: serverContent }], // Only send new message (server handles history)
                    model: selectedModel,
                    stream: true
                }),
            })

            if (!response.ok) throw new Error('Network response was not ok')

            const reader = response.body?.getReader()
            const decoder = new TextDecoder()

            if (!reader) return

            let accumulatedContent = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value)
                const lines = chunk.split('\n')

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6)
                        if (data === '[DONE]') break

                        try {
                            const parsed = JSON.parse(data)

                            // Check for Session ID event (first chunk usually)
                            if (parsed.session_id) {
                                if (!currentSessionId) {
                                    setCurrentSessionId(parsed.session_id)
                                    // Refresh list to show new title
                                    fetchSessions()
                                }
                            }

                            // Check for Message ID (sent at end)
                            if (parsed.message_id) {
                                setMessages(prev => {
                                    const newMessages = [...prev]
                                    const lastMsg = newMessages[newMessages.length - 1]
                                    if (lastMsg.role === 'assistant') {
                                        lastMsg.id = parsed.message_id
                                    }
                                    return newMessages
                                })
                            }

                            if (parsed.thought) {
                                setMessages(prev => {
                                    const newMessages = [...prev]
                                    const lastMsg = newMessages[newMessages.length - 1]
                                    if (lastMsg.role === 'assistant') {
                                        // Append thought as new line, keep last 10 lines
                                        const current = lastMsg.thoughts || ''
                                        const lines = current ? current.split('\n') : []
                                        lines.push(parsed.thought)
                                        if (lines.length > 10) lines.shift()
                                        lastMsg.thoughts = lines.join('\n')
                                    }
                                    return newMessages
                                })
                            }

                            if (parsed.token_usage) {
                                setMessages(prev => {
                                    const newMessages = [...prev]
                                    const lastMsg = newMessages[newMessages.length - 1]
                                    if (lastMsg.role === 'assistant') {
                                        lastMsg.tokenUsage = (lastMsg.tokenUsage || 0) + parsed.token_usage
                                    }
                                    return newMessages
                                })
                            }

                            if (parsed.execution_time) {
                                setMessages(prev => {
                                    const newMessages = [...prev]
                                    const lastMsg = newMessages[newMessages.length - 1]
                                    if (lastMsg.role === 'assistant') {
                                        lastMsg.executionTime = parsed.execution_time
                                        // decision_count is sent in the same event usually, or separate
                                        if (parsed.decision_count) {
                                            lastMsg.decisionCount = parsed.decision_count
                                        }
                                    }
                                    return newMessages
                                })
                            }

                            if (parsed.content) {
                                accumulatedContent += parsed.content
                                setMessages(prev => {
                                    const newMessages = [...prev]
                                    const lastMsg = newMessages[newMessages.length - 1]
                                    if (lastMsg.role === 'assistant') {
                                        lastMsg.content = accumulatedContent
                                    }
                                    return newMessages
                                })
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data', e)
                        }
                    }
                }
            }

            // Refresh sessions list after chat to update timestamps/ordering
            fetchSessions()

        } catch (error) {
            console.error('Error sending message:', error)
            setMessages(prev => {
                const newMessages = [...prev]
                const lastMsg = newMessages[newMessages.length - 1]
                lastMsg.content = 'Sorry, I encountered an error. Please check if the backend is running.'
                return newMessages
            })
        }
    }

    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900 font-sans">
            {/* Sidebar */}
            <div className="w-64 bg-gray-900 text-white flex flex-col flex-shrink-0">
                <div className="p-4 border-b border-gray-800 flex items-center gap-2 font-bold">
                    <Bot className="h-6 w-6 text-blue-400" />
                    <span>Coda Agent</span>
                </div>

                <div className="p-2">
                    <button
                        onClick={handleNewChat}
                        className="w-full flex items-center gap-2 p-3 rounded-md bg-blue-600 hover:bg-blue-700 transition-colors text-sm font-medium mb-1"
                    >
                        <Plus className="h-4 w-4" />
                        New Chat
                    </button>
                    <button
                        onClick={() => setView('analytics')}
                        className={`w-full flex items-center gap-2 p-3 rounded-md transition-colors text-sm font-medium ${view === 'analytics' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'}`}
                    >
                        <BarChart2 className="h-4 w-4" />
                        Analytics
                    </button>
                </div>

                <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
                    <div className="px-4 mt-2 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Recent Chats
                    </div>

                    <div className="flex-1 overflow-y-auto px-2 space-y-1">
                        {sessions.map((session) => (
                            <div
                                key={session.id}
                                onClick={() => { loadSession(session.id); setView('chat'); }}
                                className={`group flex items-center gap-2 p-2 rounded-md cursor-pointer mb-1 text-sm ${currentSessionId === session.id ? 'bg-gray-800 text-blue-400' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                    }`}
                            >
                                <MessageSquare className="h-4 w-4 shrink-0" />
                                <span className="truncate flex-1">{session.title || 'Untitled Chat'}</span>
                                <button
                                    onClick={(e) => deleteSession(e, session.id)}
                                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                                >
                                    <Trash2 className="h-3 w-3" />
                                </button>
                            </div>
                        ))}
                        {sessions.length === 0 && (
                            <div className="px-4 py-8 text-center text-gray-500 text-xs">
                                No recent history
                            </div>
                        )}
                    </div>

                    <div className="p-2 border-t border-gray-800">
                        <button
                            onClick={() => setShowSettings(true)}
                            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors w-full p-2 rounded-md hover:bg-gray-800"
                        >
                            <Settings className="h-4 w-4" />
                            <span className="text-sm">Settings</span>
                        </button>
                    </div>
                </div>

                <div className="p-4 border-t border-gray-800">
                    <div className="flex items-center gap-2 text-sm text-gray-400">
                        <div className={`h-2 w-2 rounded-full ${health ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span>Backend: {health ? 'Online' : 'Offline'}</span>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            {view === 'analytics' ? (
                <div className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900">
                    <Analytics />
                </div>
            ) : (
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Header */}
                    <div className="h-14 border-b bg-white dark:bg-gray-900 flex items-center justify-between px-6 shrink-0">
                        <h2 className="font-semibold text-gray-800 dark:text-gray-200 truncate max-w-[50%]">
                            {sessions.find(s => s.id === currentSessionId)?.title || 'New Chat'}
                        </h2>
                        <div className="flex items-center gap-2">
                            {currentSessionId && (
                                <>
                                    <button
                                        onClick={handleShare}
                                        className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
                                        title="Share Link"
                                    >
                                        <Share2 className="h-5 w-5" />
                                    </button>
                                    <button
                                        onClick={handleExport}
                                        className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
                                        title="Export JSON"
                                    >
                                        <Download className="h-5 w-5" />
                                    </button>
                                </>
                            )}
                            <button className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400">
                                <Settings className="h-5 w-5" />
                            </button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-auto p-6 space-y-6">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                                {msg.role === 'assistant' && (
                                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                                        <Bot className="h-5 w-5 text-blue-600" />
                                    </div>
                                )}

                                <div className={`flex flex-col gap-1 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                    <div className={`rounded-2xl px-4 py-3 whitespace-pre-wrap ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-br-none'
                                        : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
                                        }`}>
                                        {msg.attachments && msg.attachments.length > 0 && (
                                            <div className="flex flex-wrap gap-2 mb-2">
                                                {msg.attachments.map((file: any, index: number) => (
                                                    <div key={index} className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700">
                                                        <FileText className="h-4 w-4 text-blue-500" />
                                                        <span className="text-xs font-medium text-gray-700 dark:text-gray-300 max-w-[150px] truncate" title={file.filename}>
                                                            {file.filename}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                        {msg.thoughts && (
                                            <div className="mb-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-xs text-gray-500 font-mono border border-gray-100 dark:border-gray-700">
                                                <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-100 dark:border-gray-700 text-gray-400 font-semibold uppercase tracking-wider text-[10px]">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                                                    Thought Process
                                                </div>
                                                <div className="space-y-1">
                                                    {msg.thoughts.split('\n').map((line: string, i: number) => (
                                                        <div key={i} className="flex gap-2">
                                                            <span className="text-gray-300 select-none">›</span>
                                                            {line}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {msg.content}
                                        {(msg.tokenUsage || msg.executionTime || msg.id) && (
                                            <div className="text-[10px] text-gray-400 mt-1 mr-[-8px] flex justify-end opacity-70 gap-3">
                                                {msg.role === 'assistant' && msg.tokenUsage && <span>⚡ {msg.tokenUsage} tokens</span>}
                                                {msg.role === 'assistant' && msg.executionTime && <span>⏱️ {msg.executionTime.toFixed(2)}s</span>}
                                                {msg.role === 'assistant' && (msg.decisionCount > 0) && <span>🎯 {msg.decisionCount} decisions</span>}
                                                {msg.id && (
                                                    <button
                                                        onClick={() => handleFork(msg.id)}
                                                        className="ml-2 hover:text-blue-500 transition-colors"
                                                        title="Fork thread from here"
                                                    >
                                                        <GitBranch size={14} />
                                                    </button>
                                                )}
                                            </div>
                                        )}
                                        {msg.role === 'assistant' && (
                                            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                                                <button
                                                    onClick={() => msg.id && handleFeedback(msg.id, 1, idx)}
                                                    className={`p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${msg.feedback?.score === 1 ? 'text-green-500 bg-green-50' : 'text-gray-400'}`}
                                                    title="Good response"
                                                    disabled={!msg.id}
                                                >
                                                    <ThumbsUp className="h-4 w-4" />
                                                </button>
                                                <button
                                                    onClick={() => msg.id && handleFeedback(msg.id, -1, idx)}
                                                    className={`p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${msg.feedback?.score === -1 ? 'text-red-500 bg-red-50' : 'text-gray-400'}`}
                                                    title="Bad response"
                                                    disabled={!msg.id}
                                                >
                                                    <ThumbsDown className="h-4 w-4" />
                                                </button>
                                            </div>
                                        )}
                                    </div>

                                    {
                                        msg.role === 'user' && (
                                            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
                                                <div className="font-bold text-gray-600">U</div>
                                            </div>
                                        )
                                    }
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-center p-4">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            </div>
                        )}
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-white dark:bg-gray-900 border-t shrink-0">
                        <div className="max-w-4xl mx-auto relative">
                            <form onSubmit={handleSubmit}>
                                {attachments.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mb-2 px-2">
                                        {attachments.map((file, idx) => (
                                            <div key={idx} className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700">
                                                <FileText className="h-4 w-4 text-blue-500" />
                                                <span className="text-xs font-medium text-gray-700 dark:text-gray-300 max-w-[150px] truncate" title={file.filename}>
                                                    {file.filename}
                                                </span>
                                                <button
                                                    type="button"
                                                    onClick={() => removeAttachment(idx)}
                                                    className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full text-gray-500 transition-colors"
                                                >
                                                    <X className="h-3 w-3" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Message Coda Agent..."
                                    className="w-full pl-12 pr-12 py-3 rounded-xl border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                                />
                                <button
                                    type="button"
                                    onClick={() => fileInputRef.current?.click()}
                                    className="absolute left-2 top-2 p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                                >
                                    <Paperclip className="h-4 w-4" />
                                </button>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    className="hidden"
                                    onChange={handleFileUpload}
                                    accept=".pdf,.txt,.csv,.xlsx,.xls"
                                />
                                <button
                                    type="submit"
                                    disabled={!input.trim()}
                                    className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Send className="h-4 w-4" />
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            )}
            {/* Settings Dialog */}
            {showSettings && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md overflow-hidden border border-gray-700">
                        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
                            <h2 className="text-lg font-semibold dark:text-white flex items-center gap-2">
                                <Settings className="h-5 w-5" />
                                Settings
                            </h2>
                            <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-white">
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        <div className="p-4 space-y-4 max-h-[70vh] overflow-y-auto">

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Default Model
                                </label>
                                <select
                                    value={tempModel}
                                    onChange={(e) => setTempModel(e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 px-3 text-sm text-gray-100 focus:ring-2 focus:ring-blue-500"
                                >
                                    <optgroup label="OpenAI">
                                        <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
                                        <option value="gpt-4">GPT-4</option>
                                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                                    </optgroup>
                                    <optgroup label="Anthropic">
                                        <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                                        <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                                    </optgroup>
                                    <optgroup label="Google">
                                        <option value="gemini-pro">Gemini Pro</option>
                                    </optgroup>
                                </select>
                            </div>

                            <hr className="border-gray-700" />

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    OpenAI API Key
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Key className="h-4 w-4 text-gray-400" />
                                    </div>
                                    <input
                                        type="password"
                                        value={tempKeys.openai}
                                        onChange={(e) => setTempKeys({ ...tempKeys, openai: e.target.value })}
                                        placeholder="sk-..."
                                        className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 pl-10 pr-4 text-sm text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Anthropic API Key
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Key className="h-4 w-4 text-gray-400" />
                                    </div>
                                    <input
                                        type="password"
                                        value={tempKeys.anthropic}
                                        onChange={(e) => setTempKeys({ ...tempKeys, anthropic: e.target.value })}
                                        placeholder="sk-ant-..."
                                        className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 pl-10 pr-4 text-sm text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Google Gemini API Key
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Key className="h-4 w-4 text-gray-400" />
                                    </div>
                                    <input
                                        type="password"
                                        value={tempKeys.google}
                                        onChange={(e) => setTempKeys({ ...tempKeys, google: e.target.value })}
                                        placeholder="AIza..."
                                        className="w-full bg-gray-900 border border-gray-700 rounded-md py-2 pl-10 pr-4 text-sm text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                            </div>

                            <p className="text-xs text-gray-500 mt-1">
                                Keys are stored locally in your browser. Leave blank to use server defaults (if configured).
                            </p>
                        </div>
                        <div className="p-4 border-t border-gray-700 flex justify-end gap-2 bg-gray-900/50">
                            <button
                                onClick={() => setShowSettings(false)}
                                className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSaveSettings}
                                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                            >
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default App
