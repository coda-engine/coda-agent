import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface AnalyticsOverview {
    total_sessions: number;
    total_messages: number;
    total_tokens: number;
    avg_execution_time: number;
}

export interface ToolUsage {
    tool_name: string;
    count: number;
}

export interface ToolAnalytics {
    usage: ToolUsage[];
}

export interface DecisionUsage {
    category: string;
    count: number;
}

export interface DecisionAnalytics {
    usage: DecisionUsage[];
}

export const getUsageAnalytics = async (): Promise<AnalyticsOverview> => {
    const response = await axios.get(`${API_URL}/api/v1/analytics/usage`);
    return response.data;
};

export const getToolAnalytics = async (): Promise<ToolAnalytics> => {
    const response = await axios.get(`${API_URL}/api/v1/analytics/tools`);
    return response.data;
};

export const getDecisionAnalytics = async (): Promise<DecisionAnalytics> => {
    const response = await axios.get(`${API_URL}/api/v1/analytics/decisions`);
    return response.data;
};
