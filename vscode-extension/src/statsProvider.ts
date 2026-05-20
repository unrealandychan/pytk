import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

interface StatRecord {
    command: string;
    orig_chars: number;
    filt_chars: number;
    ts: string;
}

export class StatsProvider {
    private statsPath: string;
    private records: StatRecord[] = [];

    constructor() {
        this.statsPath = path.join(os.homedir(), '.pytk', 'stats.json');
        this.refresh();
    }

    refresh(): void {
        try {
            if (!fs.existsSync(this.statsPath)) return;
            const content = fs.readFileSync(this.statsPath, 'utf-8');
            this.records = content.trim().split('\n')
                .filter(l => l.trim())
                .map(l => JSON.parse(l)) as StatRecord[];
        } catch {
            this.records = [];
        }
    }

    getTotalSavingsPct(): number {
        if (this.records.length === 0) return 0;
        const totalOrig = this.records.reduce((s, r) => s + (r.orig_chars || 0), 0);
        const totalFilt = this.records.reduce((s, r) => s + (r.filt_chars || 0), 0);
        if (totalOrig === 0) return 0;
        return Math.round((1 - totalFilt / totalOrig) * 100);
    }

    getByCommand(): Record<string, {runs: number, orig: number, filt: number}> {
        const byCmd: Record<string, {runs: number, orig: number, filt: number}> = {};
        for (const r of this.records) {
            if (!byCmd[r.command]) byCmd[r.command] = {runs: 0, orig: 0, filt: 0};
            byCmd[r.command].runs++;
            byCmd[r.command].orig += r.orig_chars || 0;
            byCmd[r.command].filt += r.filt_chars || 0;
        }
        return byCmd;
    }
}
