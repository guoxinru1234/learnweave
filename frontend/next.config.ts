import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output for Docker deployment
  output: 'standalone',

  // 图片优化
  images: {
    domains: [],
    unoptimized: process.env.NODE_ENV === 'development',
  },

  // 代理：将 /api/* 和 /media/* 请求转发到后端 8002 端口
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8002/api/:path*',
      },
      {
        source: '/media/:path*',
        destination: 'http://127.0.0.1:8002/media/:path*',
      },
    ];
  },

  // Turbopack 配置
  turbopack: {},
};

export default nextConfig;
