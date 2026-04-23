import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
      <h1 className="text-4xl font-bold mb-6">CareerPath AI</h1>
      <Button variant="default">Test shadcn Button</Button>
    </main>
  );
}