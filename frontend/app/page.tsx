import ViewSummaries from '@/components/ViewSummaries'
import ModalUpload from '@/components/ModalUpload'

export default function HomePage() {
  return (
    <main className="max-w-6xl mx-auto py-10 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">📝 Meeting Summary Dashboard</h1>
        <ModalUpload />
      </div>

      <ViewSummaries />
    </main>
  )
}
