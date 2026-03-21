interface Props {
  stationNames: string[];
  origin: string;
  destination: string;
  onOriginChange: (v: string) => void;
  onDestinationChange: (v: string) => void;
  onSearch: () => void;
  loading: boolean;
}

export function SearchInputs({
  stationNames,
  origin,
  destination,
  onOriginChange,
  onDestinationChange,
  onSearch,
  loading,
}: Props) {
  if (stationNames.length === 0) {
    return (
      <div className="search-container">
        <div>Loading station names...</div>
      </div>
    );
  }

  return (
    <div className="search-container">
      <div>
        <div className="section-label">From</div>
        <select
          className="search-select"
          value={origin}
          onChange={(e) => onOriginChange(e.target.value)}
        >
          {stationNames.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <div className="section-label">To</div>
        <select
          className="search-select"
          value={destination}
          onChange={(e) => onDestinationChange(e.target.value)}
        >
          {stationNames.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      <button
        className="search-button"
        onClick={onSearch}
        disabled={loading || origin === destination}
      >
        {loading ? "Analyzing routes..." : "Find routes"}
      </button>
    </div>
  );
}
