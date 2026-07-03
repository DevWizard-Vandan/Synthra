import { cn } from "@/lib/utils";

interface CardHeaderProps {
  title: string;
  action?: React.ReactNode;
  className?: string;
}

export function CardHeader({ title, action, className }: CardHeaderProps) {
  return (
    <div className={cn("flex items-center justify-between mb-4", className)}>
      <h2 className="text-sm font-semibold text-foreground">{title}</h2>
      {action && <div>{action}</div>}
    </div>
  );
}
