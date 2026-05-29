enum AppMode {
  official,
  opensourcePlus;

  static AppMode fromString(String value) {
    return AppMode.values.firstWhere((m) => m.name == value, orElse: () => AppMode.official);
  }
}
