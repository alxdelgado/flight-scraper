import SwiftUI

struct SearchView: View {
    @State private var viewModel = SearchViewModel()
    @State private var showingOriginPicker = false
    @State private var showingDestPicker   = false
    @State private var navigateToSearching = false

    private var searchButtonDisabled: Bool {
        viewModel.originCode.isEmpty || viewModel.destinationQuery.isEmpty
    }

    var body: some View {
        NavigationStack {
            Form {
                routeSection
                datesSection
                if let error = viewModel.errorMessage {
                    errorSection(error)
                }
            }
            .navigationTitle("Search Flights")
            .navigationBarTitleDisplayMode(.large)
            .toolbar { searchToolbarButton }
            .sheet(isPresented: $showingOriginPicker) {
                AirportPickerView(field: .origin, viewModel: viewModel)
            }
            .sheet(isPresented: $showingDestPicker) {
                AirportPickerView(field: .destination, viewModel: viewModel)
            }
            .navigationDestination(isPresented: $navigateToSearching) {
                // SearchingView is built in Feature 6
                SearchingPlaceholderView(viewModel: viewModel)
            }
            .onChange(of: viewModel.searchPhase) { _, phase in
                if phase == .searching {
                    navigateToSearching = true
                }
            }
        }
    }

    // MARK: - Sections

    private var routeSection: some View {
        Section("Route") {
            // Origin
            Button {
                showingOriginPicker = true
            } label: {
                LabeledContent {
                    Text(viewModel.originCode.isEmpty ? "Airport or city" : viewModel.originCode)
                        .foregroundStyle(viewModel.originCode.isEmpty ? .secondary : .primary)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                } label: {
                    Label("From", systemImage: "airplane.departure")
                }
            }
            .foregroundStyle(.primary)

            // Destination
            Button {
                showingDestPicker = true
            } label: {
                LabeledContent {
                    Text(viewModel.destinationQuery.isEmpty
                         ? "Airport, city, or region"
                         : viewModel.destinationQuery)
                        .foregroundStyle(viewModel.destinationQuery.isEmpty ? .secondary : .primary)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                        .lineLimit(1)
                } label: {
                    Label("To", systemImage: "airplane.arrival")
                }
            }
            .foregroundStyle(.primary)
        }
    }

    private var datesSection: some View {
        Section("Dates") {
            Picker("Trip type", selection: $viewModel.isRoundTrip) {
                Text("Round-trip").tag(true)
                Text("One-way").tag(false)
            }
            .pickerStyle(.segmented)
            .listRowInsets(.init(top: 8, leading: 16, bottom: 8, trailing: 16))

            DatePicker(
                "Depart",
                selection: $viewModel.departDate,
                in: Date()...,
                displayedComponents: .date
            )

            if viewModel.isRoundTrip {
                DatePicker(
                    "Return",
                    selection: Binding(
                        get: {
                            viewModel.returnDate
                                ?? Calendar.current.date(byAdding: .day, value: 7,
                                                         to: viewModel.departDate)
                                ?? viewModel.departDate
                        },
                        set: { viewModel.returnDate = $0 }
                    ),
                    in: viewModel.departDate...,
                    displayedComponents: .date
                )
            }
        }
    }

    @ViewBuilder
    private func errorSection(_ message: String) -> some View {
        Section {
            Label(message, systemImage: "exclamationmark.triangle.fill")
                .foregroundStyle(.red)
        }
    }

    private var searchToolbarButton: some ToolbarContent {
        ToolbarItem(placement: .primaryAction) {
            Button {
                viewModel.startSearch()
            } label: {
                Text("Search")
                    .fontWeight(.semibold)
            }
            .buttonStyle(.borderedProminent)
            .disabled(searchButtonDisabled)
        }
    }
}

// MARK: - Placeholder until Feature 6 builds the real searching screen

struct SearchingPlaceholderView: View {
    @Bindable var viewModel: SearchViewModel

    var body: some View {
        VStack(spacing: 24) {
            ProgressView()
                .scaleEffect(1.5)
            Text(viewModel.searchPhase.isSearching ? "Searching…" : "Done")
                .font(.title3)
                .fontWeight(.medium)
            Text("\(viewModel.completedSessions) of \(viewModel.totalSessions) airports searched")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Button("Cancel", role: .cancel) {
                viewModel.cancelSearch()
            }
        }
        .navigationTitle("Searching")
        .navigationBarBackButtonHidden(viewModel.searchPhase.isSearching)
    }
}

#Preview("Search Form") {
    SearchView()
}
