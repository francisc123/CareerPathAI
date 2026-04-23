/** @type {import('next').NextConfig} */
const nextConfig = {
  // Activează build-ul standalone pentru containere Docker eficiente
  output: "standalone",
  
  async rewrites() {
    return [
      {
        // Redirecționează apelurile de tip /api către URL-ul Gateway-ului
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;