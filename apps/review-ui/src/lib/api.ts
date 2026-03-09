export async function fetchReview(threadId: string) {
  const res = await fetch(`/api/reviews/${threadId}`);
  return await res.json();
}
