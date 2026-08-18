use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::collections::HashSet;

const EPS: f64 = 1e-12;

/// Compute one Hybrid DeGroot update:
///
/// x_v(t+1) = (1 - sum_{(u,v) in E'} I_uv) x_v(t)
///            + sum_{(u,v) in E'} I_uv x_u(t)
///
/// The edges are directed as u -> v, meaning that u influences v.
#[pyfunction]
fn next_opinions(
    opinions: Vec<f64>,
    edges: Vec<(usize, usize, f64)>,
    enabled_edges: Vec<(usize, usize)>,
) -> PyResult<Vec<f64>> {
    let n = opinions.len();

    for (i, value) in opinions.iter().enumerate() {
        if !value.is_finite() || *value < 0.0 || *value > 1.0 {
            return Err(PyValueError::new_err(format!(
                "opinion at index {i} must be finite and in [0, 1]"
            )));
        }
    }

    let enabled: HashSet<(usize, usize)> = enabled_edges.into_iter().collect();
    let mut next = opinions.clone();
    let mut incoming_sum = vec![0.0_f64; n];

    for (u, v, influence) in edges {
        if u >= n || v >= n {
            return Err(PyValueError::new_err(format!(
                "edge index out of bounds: {u} -> {v} for n={n}"
            )));
        }
        if !influence.is_finite() || influence <= 0.0 {
            return Err(PyValueError::new_err("influences must be finite and positive"));
        }

        if enabled.contains(&(u, v)) {
            incoming_sum[v] += influence;
            if incoming_sum[v] > 1.0 + EPS {
                return Err(PyValueError::new_err(format!(
                    "incoming influence for node index {v} exceeds 1"
                )));
            }

            // Equivalent to:
            // (1 - sum I_uv) * x_v + sum I_uv * x_u,
            // but accumulated edge by edge.
            next[v] += influence * (opinions[u] - opinions[v]);
        }
    }

    for value in &mut next {
        // Protect only against tiny floating-point noise.
        if *value < 0.0 && *value > -EPS {
            *value = 0.0;
        } else if *value > 1.0 && *value < 1.0 + EPS {
            *value = 1.0;
        }

        if *value < 0.0 || *value > 1.0 || !value.is_finite() {
            return Err(PyValueError::new_err("computed opinion went outside [0, 1]"));
        }
    }

    Ok(next)
}

#[pymodule]
fn opinion_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(next_opinions, m)?)?;
    Ok(())
}
