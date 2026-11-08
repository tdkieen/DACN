import { Card } from "@/components/ui/card";

export function EmptyState({ message }: { message: string }) {
  return (
    <Card className="flex items-center justify-center border-dashed p-10 text-sm text-muted-foreground">
      {message}
    </Card>
  );
}
