import { ReversibleOverridesMap } from '@krassowski/jupyterlab-lsp/lib/overrides/maps';
import { overrides } from './overrides';
import { expect } from 'chai';


describe('data-vault overrides', () => {

  describe('line magics', () => {
    let line_magics = new ReversibleOverridesMap(
      overrides.filter(override => override.scope == 'line')
    );

    it('open_vault magic works', () => {
      let line = '%open_vault -p data/storage.zip';
      let override = line_magics.override_for(line);
      expect(override).to.equal(`import data_vault


_vault_magics = data_vault.VaultMagics()
_vault_magics.open_vault("-p data/storage.zip")`);
      let reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);
    });

    it('store command works', () => {
      let line = '%vault store salaries in datasets';
      let override = line_magics.override_for(line);
      expect(override).to.equal(`data_vault.actions.StoreAction(_vault_magics.current_vault).store_in_module({"in": "datasets", "store_value": [salaries]})`);
      let reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);

      line = '%vault store salaries in datasets with to_csv';
      override = line_magics.override_for(line);
      expect(override).to.equal(`data_vault.actions.StoreAction(_vault_magics.current_vault).store_in_module({"in": "datasets", "store_value": [salaries], "with": to_csv})`);
      reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);

      line = '%vault store salaries, cities in datasets';
      override = line_magics.override_for(line);
      expect(override).to.equal(`data_vault.actions.StoreAction(_vault_magics.current_vault).store_in_module({"in": "datasets", "store_value": [salaries, cities]})`);
      reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);
    });

    it('import from command works', () => {
      let line = '%vault import salaries from datasets';
      let override = line_magics.override_for(line);
      expect(override).to.equal(`salaries = data_vault.actions.ImportAction(_vault_magics.current_vault).from_module_import({"import": "salaries", "from": "datasets"})`);
      let reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);

      line = '%vault import salaries from datasets as salaries_dataset';
      override = line_magics.override_for(line);
      expect(override).to.equal(`salaries_dataset = data_vault.actions.ImportAction(_vault_magics.current_vault).from_module_import_as({"import": "salaries", "from": "datasets", "as": "salaries_dataset"})`);
      reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);

      line = '%vault import salaries, cities from datasets';
      override = line_magics.override_for(line);
      expect(override).to.equal(`salaries, cities = data_vault.actions.ImportAction(_vault_magics.current_vault).from_module_import({"import": "salaries, cities", "from": "datasets"})`);
      reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);
    });

    it('from import command works', () => {
      let line = '%vault from datasets import salaries';
      let override = line_magics.override_for(line);
      expect(override).to.equal(`salaries = data_vault.actions.ImportAction(_vault_magics.current_vault).from_module_import({"from": "datasets", "import": "salaries"})`);
      let reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);

      line = '%vault from datasets import salaries as salaries_dataset';
      override = line_magics.override_for(line);
      expect(override).to.equal(`salaries_dataset = data_vault.actions.ImportAction(_vault_magics.current_vault).from_module_import_as({"from": "datasets", "import": "salaries", "as": "salaries_dataset"})`);
      reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);

      line = '%vault from datasets import salaries with read_excel';
      override = line_magics.override_for(line);
      expect(override).to.equal(`salaries = data_vault.actions.ImportAction(_vault_magics.current_vault).from_module_import({"from": "datasets", "import": "salaries", "with": read_excel})`);
      reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);

      /* Known failure:
      line = '%vault from datasets import salaries, cities';
      override = line_magics.override_for(line);
      expect(override).to.equal(`salaries, cities = data_vault.actions.ImportAction(_vault_magics.current_vault).from_module_import({"from": "datasets", "import": "salaries, cities"]})`);
      reverse = line_magics.reverse.override_for(override);
      expect(reverse).to.equal(line);
       */
    });

  });
});
