import { IScopedCodeOverride } from '@krassowski/jupyterlab-lsp/lib/overrides/tokens';

function args_pattern(max_n: number) {
  return '(\\S+)' + ('(?:, ?(\\S+))?'.repeat(max_n - 1));
}

function parse_args(args: string[]) {
  return args.filter(arg => typeof arg !== "undefined").join(', ');
}

const ARGS = args_pattern(10)


class Optional {
  constructor(public id: string, private escape: boolean = true, private variablePattern: string = '(\\S+)') {
  }

  get pattern() {
    return `(?: ${this.id} ${this.variablePattern})?`
  }

  get reversePattern() {
    let variablePattern = this.variablePattern
    if (this.escape) {
      variablePattern = `"${variablePattern}"`
    }
    return `(?:, "${this.id}": ${variablePattern})?`
  }

  prepare(value: string) {
    return typeof value !== "undefined" ? `, "${this.id}": ${this.escape ? '"' + value + '"' : value}` : '';
  }

  prepareReverse(value: string) {
    return typeof value !== "undefined" ? ` ${this.id} ${value}` : '';
  }
}

const OPTIONALS = [
  new Optional('with', false),
  new Optional('as')
]

class Optionals {
  constructor(private optionals: Optional[]) {
  }

  get patterns(): string {
    return this.optionals.map(o => o.pattern).join('')
  }

  get reversePatterns(): string {
    return this.optionals.map(o => o.reversePattern).join('')
  }

  parseAll(args: string[], offset: number): Map<string, string> {
    return new Map(this.optionals.map((o, i) => [o.id, args[offset + i]]))
  }

  prepareAll(args: string[], offset: number): string {
    return this.optionals.map((o, i) => o.prepare(args[offset + i])).join('')
  }

  prepareReverseAll(args: string[], offset: number): string {
    return this.optionals.map((o, i) => o.prepareReverse(args[offset + i])).join('')
  }
}

const optionals = new Optionals(OPTIONALS)

export let overrides: IScopedCodeOverride[] = [
  {
    pattern: '%open_vault (.*)(\n)?',
    replacement: (match, ...args) => {
      return `import data_vault


_vault_magics = data_vault.VaultMagics()
_vault_magics.open_vault("${args[0]}")`;
    },
    scope: 'line',
    reverse: {
      pattern: `import data_vault


_vault_magics = data_vault\\.VaultMagics\\(\\)
_vault_magics\\.open_vault\\("(.*?)"\\)`,
      replacement: (match, ...args) => {
        return `%open_vault ${args[0]}`;
      },
      scope: 'line'
    }
  },
  {
    pattern: `%vault store ${ARGS} in (\\S+)${optionals.patterns}(\n)?`,
    replacement: (match, ...args) => {
      let to_store = parse_args(args.slice(0, 10))
      return `data_vault.actions.StoreAction(_vault_magics.current_vault).store_in_module({"in": "${args[10]}", "store_value": [${to_store}]${optionals.prepareAll(args, 11)}})`;
    },
    scope: 'line',
    reverse: {
      pattern: `data_vault\\.actions\\.StoreAction\\(_vault_magics\\.current_vault\\)\\.store_in_module\\({"in": "(\\S+?)", "store_value": \\[${ARGS}\\]${optionals.reversePatterns}}\\)`,
      replacement: (match, ...args) => {
        let to_store = parse_args(args.slice(1, 11))
        return `%vault store ${to_store} in ${args[0]}${optionals.prepareReverseAll(args, 11)}`;
      },
      scope: 'line'
    }
  },
  {
    pattern: `%vault import ${ARGS} from (\\S+)${optionals.patterns}(\n)?`,
    replacement: (match, ...args) => {
      let to_import = parse_args(args.slice(0, 10))
      let optional_args = optionals.parseAll(args, 11);
      let optional_as = optional_args.get('as')
      let assignment = optional_as ? optional_as : to_import;
      let method = optional_as ? 'from_module_import_as' : 'from_module_import';
      return `${assignment} = data_vault.actions.ImportAction(_vault_magics.current_vault).${method}({"import": "${to_import}", "from": "${args[10]}"${optionals.prepareAll(args, 11)}})`;
    },
    scope: 'line',
    reverse: {
      pattern: `${ARGS} = data_vault\\.actions\\.ImportAction\\(_vault_magics\\.current_vault\\)\\.(?:from_module_import_as|from_module_import)\\({"import": "${ARGS}", "from": "(\\S+?)"${optionals.reversePatterns}}\\)`,
      replacement: (match, ...args) => {
        let to_import = parse_args(args.slice(10, 20))
        return `%vault import ${to_import} from ${args[20]}${optionals.prepareReverseAll(args, 21)}`;
      },
      scope: 'line'
    }
  },
  {
    pattern: `%vault from (\\S+) import ${ARGS}${optionals.patterns}(\n)?`,
    replacement: (match, ...args) => {
      let to_import = parse_args(args.slice(1, 10))
      let optional_args = optionals.parseAll(args, 11);
      let optional_as = optional_args.get('as')
      let assignment = optional_as ? optional_as : to_import;
      let method = optional_as ? 'from_module_import_as' : 'from_module_import';
      return `${assignment} = data_vault.actions.ImportAction(_vault_magics.current_vault).${method}({"from": "${args[0]}", "import": "${to_import}"${optionals.prepareAll(args, 11)}})`;
    },
    scope: 'line',
    reverse: {
      pattern: `${ARGS} = data_vault\\.actions\\.ImportAction\\(_vault_magics\\.current_vault\\)\\.(?:from_module_import_as|from_module_import)\\({"from": "(\\S+?)", "import": "${ARGS}"${optionals.reversePatterns}}\\)`,
      replacement: (match, ...args) => {
        let to_import = parse_args(args.slice(11, 21))
        return `%vault from ${args[10]} import ${to_import}${optionals.prepareReverseAll(args, 21)}`;
      },
      scope: 'line'
    }
  }
];
