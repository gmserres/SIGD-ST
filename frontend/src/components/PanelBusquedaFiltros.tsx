import { useId, useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Search,
  SlidersHorizontal,
  X,
} from 'lucide-react';

type FiltroRapido = {
  value: string;
  label: string;
  disabled?: boolean;
};

type OpcionFiltro = {
  value: string;
  label: string;
};

type FiltroAvanzado = {
  key: string;
  label: string;
  type: 'select' | 'date';
  placeholder?: string;
  options?: readonly OpcionFiltro[];
  disabled?: boolean;
};

type FiltroActivo = {
  key: string;
  label: string;
  onRemove: () => void;
};

type PanelBusquedaFiltrosProps = {
  placeholder?: string;
  value: string;
  onSearchChange: (value: string) => void;
  quickFilters: readonly FiltroRapido[];
  activeQuickFilter: string;
  onQuickFilterChange: (value: string) => void;
  advancedFilters: readonly FiltroAvanzado[];
  advancedFilterValues: Record<string, string>;
  onAdvancedFilterChange: (key: string, value: string) => void;
  activeFilters: readonly FiltroActivo[];
  canClearFilters: boolean;
  onClearFilters: () => void;
};

export function PanelBusquedaFiltros({
  placeholder = 'Buscar...',
  value,
  onSearchChange,
  quickFilters,
  activeQuickFilter,
  onQuickFilterChange,
  advancedFilters,
  advancedFilterValues,
  onAdvancedFilterChange,
  activeFilters,
  canClearFilters,
  onClearFilters,
}: PanelBusquedaFiltrosProps) {
  const filtrosAvanzadosId = useId();
  const [filtrosAvanzadosVisibles, setFiltrosAvanzadosVisibles] =
    useState(false);

  return (
    <section
      className="card operational-filter-panel"
      aria-label="Búsqueda y filtros"
    >
      <label className="operational-search-field">
        <Search aria-hidden="true" />
        <input
          type="search"
          value={value}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={placeholder}
        />
      </label>

      <div
        className="operational-quick-filters"
        aria-label="Filtros rápidos"
      >
        {quickFilters.map((filtro) => (
          <button
            className={
              activeQuickFilter === filtro.value ? 'active' : ''
            }
            type="button"
            key={filtro.value}
            aria-pressed={activeQuickFilter === filtro.value}
            disabled={filtro.disabled}
            onClick={() => onQuickFilterChange(filtro.value)}
          >
            {filtro.label}
          </button>
        ))}
      </div>

      <div className="operational-filter-footer">
        <button
          className="operational-advanced-toggle"
          type="button"
          aria-expanded={filtrosAvanzadosVisibles}
          aria-controls={filtrosAvanzadosId}
          onClick={() =>
            setFiltrosAvanzadosVisibles((visible) => !visible)
          }
        >
          <SlidersHorizontal aria-hidden="true" />
          <span>Filtros avanzados</span>
          {filtrosAvanzadosVisibles ? (
            <ChevronUp aria-hidden="true" />
          ) : (
            <ChevronDown aria-hidden="true" />
          )}
        </button>

        <button
          className="operational-clear-filters"
          type="button"
          disabled={!canClearFilters}
          onClick={onClearFilters}
        >
          Limpiar todo
        </button>
      </div>

      {filtrosAvanzadosVisibles && (
        <div
          className="operational-advanced-filters"
          id={filtrosAvanzadosId}
        >
          {advancedFilters.map((filtro) => (
            <label key={filtro.key}>
              {filtro.label}
              {filtro.type === 'select' ? (
                <select
                  value={advancedFilterValues[filtro.key] ?? ''}
                  disabled={filtro.disabled}
                  onChange={(event) =>
                    onAdvancedFilterChange(filtro.key, event.target.value)
                  }
                >
                  <option value="">{filtro.placeholder ?? 'Todos'}</option>
                  {filtro.options?.map((opcion) => (
                    <option key={opcion.value} value={opcion.value}>
                      {opcion.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="date"
                  value={advancedFilterValues[filtro.key] ?? ''}
                  disabled={filtro.disabled}
                  onChange={(event) =>
                    onAdvancedFilterChange(filtro.key, event.target.value)
                  }
                />
              )}
            </label>
          ))}
        </div>
      )}

      {activeFilters.length > 0 && (
        <div
          className="operational-active-filters"
          aria-label="Filtros activos"
        >
          {activeFilters.map((filtro) => (
            <button
              type="button"
              key={filtro.key}
              onClick={filtro.onRemove}
              aria-label={`Quitar filtro ${filtro.label}`}
            >
              <span>{filtro.label}</span>
              <X aria-hidden="true" />
            </button>
          ))}
        </div>
      )}

    </section>
  );
}
