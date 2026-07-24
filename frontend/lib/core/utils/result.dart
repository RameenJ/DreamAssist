import 'package:equatable/equatable.dart';

/// Represents the result of an operation that can either succeed or fail
abstract class Result<T> extends Equatable {
  const Result();

  /// Returns true if this is a success result
  bool get isSuccess => this is Success<T>;

  /// Returns true if this is a failure result
  bool get isFailure => this is Failure<T>;

  /// Returns the data if this is a success, or null if it's a failure
  T? get dataOrNull => isSuccess ? (this as Success<T>).data : null;

  /// Returns the error message if this is a failure, or null if it's a success
  String? get errorOrNull => isFailure ? (this as Failure<T>).message : null;

  /// Executes different callbacks based on whether this is a success or failure
  R when<R>({
    required R Function(T data) success,
    required R Function(String message) failure,
  }) {
    if (this is Success<T>) {
      return success((this as Success<T>).data);
    } else {
      return failure((this as Failure<T>).message);
    }
  }
}

/// Success result containing data
class Success<T> extends Result<T> {
  final T data;

  const Success(this.data);

  @override
  List<Object?> get props => [data];
}

/// Failure result containing an error message
class Failure<T> extends Result<T> {
  final String message;
  final String? code;

  const Failure(this.message, {this.code});

  @override
  List<Object?> get props => [message, code];
}
