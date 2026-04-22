import { MapPin, Building2, ExternalLink } from "lucide-react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

interface Props {
  title: string;
  company: string;
  location: string;
  source: "LinkedIn" | "Indeed" | "eJobs";
  match: number;
  coverLetter: string;
}

export function JobCard({ title, company, location, source, match, coverLetter }: Props) {
  return (
    <Card className="bg-gray-900 border-gray-800 text-white overflow-hidden hover:border-primary/50 transition-colors">
      <CardContent className="pt-6">
        <div className="flex justify-between items-start mb-4">
          <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
            {source}
          </Badge>
          <div className="text-right">
            <span className="text-sm font-bold text-green-400 bg-green-400/10 px-2 py-1 rounded">
              {match}% Match
            </span>
          </div>
        </div>
        <h3 className="text-lg font-bold truncate">{title}</h3>
        <div className="flex items-center gap-2 text-gray-400 text-sm mt-2">
          <Building2 size={14} /> <span>{company}</span>
        </div>
        <div className="flex items-center gap-2 text-gray-400 text-sm mt-1">
          <MapPin size={14} /> <span>{location}</span>
        </div>
      </CardContent>
      <CardFooter className="bg-gray-800/50 border-t border-gray-800 gap-2">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="secondary" size="sm" className="w-full">Cover Letter</Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-900 text-white border-gray-800">
            <DialogHeader>
              <DialogTitle>Cover Letter - {company}</DialogTitle>
            </DialogHeader>
            <div className="mt-4 text-gray-300 whitespace-pre-wrap">{coverLetter}</div>
          </DialogContent>
        </Dialog>
        <Button size="icon" variant="outline" className="shrink-0 border-gray-700">
          <ExternalLink size={16} />
        </Button>
      </CardFooter>
    </Card>
  );
}