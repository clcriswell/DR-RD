import { doc, setDoc, serverTimestamp } from 'firebase/firestore';
import { db } from '../firebase';
import { slugify } from '../utils/slugify';

export async function upsertProjectByName(name: string, data: Record<string, any> = {}) {
  const slug = slugify(name || '');
  if (!slug) throw new Error('Project name is required.');
  const ref = doc(db, 'existingProjects', slug);
  const base = {
    name,
    slug,
    updatedAt: serverTimestamp(),
    createdAt: serverTimestamp(),
  };
  await setDoc(ref, { ...base, ...data }, { merge: true });
  return { id: slug, ref };
}
