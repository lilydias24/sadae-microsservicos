import { Skeleton, Card } from '../ui'

export function BillSkeleton() {
  return (
    <div className="border border-gray-200 rounded-lg p-4 animate-pulse">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-2">
            <div className="flex items-center space-x-2">
              <span>💰</span>
              <Skeleton className="h-4 w-20" />
            </div>
            <div className="flex items-center space-x-2">
              <span>💧</span>
              <Skeleton className="h-4 w-16" />
            </div>
            <div className="flex items-center space-x-2">
              <span>📅</span>
              <Skeleton className="h-4 w-28" />
            </div>
          </div>
          
          <Skeleton className="h-3 w-48" />
        </div>
        
        <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-28" />
        </div>
      </div>
    </div>
  )
}

export function BillListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, index) => (
        <BillSkeleton key={index} />
      ))}
    </div>
  )
}

export function StatCardSkeleton() {
  return (
    <Card className="p-6">
      <div className="flex items-center">
        <div className="p-3 bg-gray-100 rounded-lg animate-pulse">
          <Skeleton className="w-6 h-6" />
        </div>
        <div className="ml-4 space-y-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-6 w-12" />
        </div>
      </div>
    </Card>
  )
}