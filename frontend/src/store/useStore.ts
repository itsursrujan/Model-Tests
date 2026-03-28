import { create } from 'zustand'

interface StoreState {
    status: string;
    credits: number;
    setStatus: (status: string) => void;
    setCredits: (credits: number) => void;
}

export const useStore = create<StoreState>((set) => ({
    status: 'READY',
    credits: 100,
    setStatus: (status) => set({ status }),
    setCredits: (credits) => set({ credits })
}));
