import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

export class FilterEngine {
    private pytkPath: string;

    constructor(pytkPath: string = 'pytk') {
        this.pytkPath = pytkPath;
    }

    async runGain(): Promise<string> {
        try {
            const { stdout } = await execFileAsync(this.pytkPath, ['gain']);
            return stdout;
        } catch (err: unknown) {
            if (err instanceof Error) {
                return `Error running pytk gain: ${err.message}\n\nMake sure pytk is installed: uv tool install pytk`;
            }
            return 'Unknown error running pytk gain';
        }
    }

    async isAvailable(): Promise<boolean> {
        try {
            await execFileAsync(this.pytkPath, ['--version']);
            return true;
        } catch {
            return false;
        }
    }
}
