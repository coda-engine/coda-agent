import React, { useEffect, useState } from 'react';
import { getUsageAnalytics, getToolAnalytics, getDecisionAnalytics, AnalyticsOverview, ToolAnalytics, DecisionAnalytics } from '../api/analytics';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Loader2 } from 'lucide-react';

export default function Analytics() {
    const [data, setData] = useState<AnalyticsOverview | null>(null);
    const [toolData, setToolData] = useState<ToolAnalytics | null>(null);
    const [decisionData, setDecisionData] = useState<DecisionAnalytics | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            getUsageAnalytics(),
            getToolAnalytics(),
            getDecisionAnalytics()
        ]).then(([usage, tools, decisions]) => {
            setData(usage);
            setToolData(tools);
            setDecisionData(decisions);
            setLoading(false);
        }).catch(e => {
            console.error("Failed to load analytics", e);
            setLoading(false);
        });
    }, []);

    if (loading) {
        return <div className="flex justify-center items-center h-screen"><Loader2 className="animate-spin" /></div>;
    }

    // Transform for simple visualization
    const chartData = [
        { name: 'Sessions', value: data?.total_sessions },
        { name: 'Messages', value: data?.total_messages },
    ];

    const toolChartData = toolData?.usage || [];
    const decisionChartData = decisionData?.usage.map(d => ({ name: d.category, value: d.count })) || [];

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card title="Total Sessions" value={data?.total_sessions} />
                <Card title="Total Messages" value={data?.total_messages} />
                <Card title="Total Tokens" value={data?.total_tokens?.toLocaleString()} />
                <Card title="Avg Execution Time" value={`${data?.avg_execution_time}s`} />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-4 rounded-lg shadow h-96 border border-gray-200">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">Volume Overview</h2>
                    <ResponsiveContainer width="100%" height="90%">
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="value" fill="#3B82F6" barSize={50} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="bg-white p-4 rounded-lg shadow h-96 border border-gray-200">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">Tool Usage</h2>
                    <ResponsiveContainer width="100%" height="90%">
                        <BarChart data={toolChartData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" />
                            <YAxis dataKey="tool_name" type="category" width={100} />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="count" fill="#10B981" barSize={30} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Additional Charts Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Decision Types */}
                <div className="bg-white p-4 rounded-lg shadow h-96 border border-gray-200">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">Decision Types</h2>
                    <ResponsiveContainer width="100%" height="90%">
                        <BarChart data={decisionChartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="value" fill="#8B5CF6" barSize={50} name="Decisions" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}

function Card({ title, value }: { title: string, value: any }) {
    return (
        <div className="bg-white p-4 rounded-lg shadow border border-gray-100">
            <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
            <p className="text-3xl font-bold mt-2 text-gray-900">{value}</p>
        </div>
    )
}
