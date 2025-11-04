import { cn } from '../../utils/cn'

interface SkeletonProps {
  className?: string
  rows?: number
}

export function Skeleton({ className, rows = 1 }: SkeletonProps) {
  if (rows === 1) {
    return (
      <div className={cn(
        'animate-pulse bg-gray-200 rounded',
        className
      )} />
    )
  }

  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className={cn(
            'animate-pulse bg-gray-200 rounded h-4',
            index === rows - 1 && 'w-3/4', // Last row is shorter
            className
          )}
        />
      ))}
    </div>
  )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="flex items-center space-x-4 p-4">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-16" />
        </div>
      ))}
    </div>
  )
}

export function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="space-y-4">
        <Skeleton className="h-6 w-1/3" />
        <Skeleton rows={3} />
        <div className="flex justify-between">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-20" />
        </div>
      </div>
    </div>
  )
}