// app/(main)/features/page.tsx
import { redirect } from 'next/navigation';

export default function FeaturesPage() {
  // Redirect to homepage which shows all features
  redirect('/');
}


// app/(main)/revenue-dashboard/page.tsx
import { redirect } from 'next/navigation';

export default function RevenueDashboardPage() {
  // Redirect to main dashboard which includes revenue metrics
  redirect('/dashboard');
}
