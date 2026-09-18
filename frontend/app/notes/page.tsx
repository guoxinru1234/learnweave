'use client';
import { useSearchParams } from 'next/navigation';
import NoteSection from '@/components/NoteSection';
import WrongQuestionBook from '@/components/WrongQuestionBook';
export default function NotesPage(){const p=useSearchParams();return p.get('category')==='wrong_question'?<WrongQuestionBook/>:<NoteSection lectureId={0} compact={false}/>}
