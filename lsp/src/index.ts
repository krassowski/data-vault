import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import { ILSPCodeExtractorsManager } from '@krassowski/jupyterlab-lsp/lib/tokens';
import { ILSPCodeOverridesManager } from '@krassowski/jupyterlab-lsp/lib/overrides/tokens';
import { overrides } from './overrides';

const plugin: JupyterFrontEndPlugin<void> = {
  id: '@krassowski/data-vault-lsp',
  requires: [ILSPCodeExtractorsManager, ILSPCodeOverridesManager],
  activate: (
    app,
    extractors_manager: ILSPCodeExtractorsManager,
    overrides_manager: ILSPCodeOverridesManager
  ) => {
    for (let override of overrides) {
      overrides_manager.register(override, 'python');
    }
  },
  autoStart: true
};

export default plugin;
