import { initializeApp, applicationDefault } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';

initializeApp({ credential: applicationDefault() });
const db = getFirestore();

function isUuidv4(id) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id);
}

async function main() {
  const snap = await db.collection('existingProjects').get();
  let count = 0;
  for (const doc of snap.docs) {
    const data = doc.data() || {};
    if (
      isUuidv4(doc.id) &&
      (data.idea === '' || data.idea === undefined) &&
      (data.cycle === 0 || data.cycle === undefined) &&
      !data.name &&
      !data.slug
    ) {
      await doc.ref.delete();
      count++;
      console.log('Deleted orphan project', doc.id);
    }
  }
  console.log('Cleanup complete, removed', count, 'docs');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
