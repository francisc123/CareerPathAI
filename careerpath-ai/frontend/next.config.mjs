/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  
  // În versiunile mai noi, se pune sub 'experimental' sau se lasă pe auto
  experimental: {
    optimizePackageImports: ['lucide-react', 'framer-motion', '@radix-ui/react-dialog'],
  },

  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;