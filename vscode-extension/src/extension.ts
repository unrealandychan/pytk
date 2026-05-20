import * as vscode from 'vscode';
import { StatsProvider } from './statsProvider';
import { FilterEngine } from './filterEngine';

let statusBarItem: vscode.StatusBarItem;
let statsProvider: StatsProvider;
let filterEngine: FilterEngine;
let enabled = true;

export function activate(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('pytk');
    enabled = config.get('enabled', true);
    
    statsProvider = new StatsProvider();
    filterEngine = new FilterEngine(config.get('pytk_path', 'pytk'));

    // Status bar
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'pytk.showSavings';
    context.subscriptions.push(statusBarItem);
    updateStatusBar();

    // Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytk.enable', () => {
            enabled = true;
            vscode.window.showInformationMessage('pytk: Token filtering enabled');
            updateStatusBar();
        }),
        vscode.commands.registerCommand('pytk.disable', () => {
            enabled = false;
            vscode.window.showInformationMessage('pytk: Token filtering disabled');
            updateStatusBar();
        }),
        vscode.commands.registerCommand('pytk.showSavings', async () => {
            const output = await filterEngine.runGain();
            const panel = vscode.window.createWebviewPanel(
                'pytkSavings', 'pytk Token Savings', vscode.ViewColumn.One,
                { enableScripts: false }
            );
            panel.webview.html = `<html><body><pre style="font-family:monospace;padding:20px">${escapeHtml(output)}</pre></body></html>`;
        })
    );

    // Terminal data listener — intercept and filter
    if (vscode.window.onDidWriteTerminalData) {
        context.subscriptions.push(
            vscode.window.onDidWriteTerminalData(async (_event) => {
                if (!enabled) return;
                // Note: VS Code terminal data interception is read-only in current API.
                // This handler tracks output for stats purposes.
                // Full interception requires shell integration (future API).
                statsProvider.refresh();
                updateStatusBar();
            })
        );
    }

    // Shell integration for pytk hook
    if (vscode.window.onDidChangeTerminalShellIntegration) {
        context.subscriptions.push(
            vscode.window.onDidChangeTerminalShellIntegration((event) => {
                const integration = event.shellIntegration;
                if (integration && enabled) {
                    // Suggest enabling pytk hook
                    vscode.window.showInformationMessage(
                        'pytk: Run `pytk hook enable` to intercept commands automatically.',
                        'Run now'
                    ).then(selection => {
                        if (selection === 'Run now') {
                            const terminal = vscode.window.activeTerminal;
                            terminal?.sendText('pytk hook enable');
                        }
                    });
                }
            })
        );
    }

    if (config.get('showStatusBar', true)) {
        statusBarItem.show();
    }
}

function updateStatusBar() {
    const savings = statsProvider.getTotalSavingsPct();
    if (enabled && savings > 0) {
        statusBarItem.text = `$(zap) pytk: ${savings}% saved`;
        statusBarItem.tooltip = 'Click to see pytk token savings';
    } else if (enabled) {
        statusBarItem.text = `$(zap) pytk: active`;
        statusBarItem.tooltip = 'pytk token filtering active';
    } else {
        statusBarItem.text = `$(zap) pytk: off`;
    }
}

function escapeHtml(text: string): string {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export function deactivate() {}
