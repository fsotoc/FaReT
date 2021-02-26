#! /usr/bin/env python
#
def beta_cdf ( x, a, b ):

#*****************************************************************************80
#
## BETA_CDF evaluates the Beta CDF.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    04 March 2016
#
#  Author:
#
#    John Burkardt
#
#  Parameters:
#
#    Input, real X, the argument of the CDF.
#
#    Input, real A, B, the parameters of the PDF.
#    0.0D+00 < A,
#    0.0D+00 < B.
#
#    Output, real CDF, the value of the CDF.
#
  from beta_inc import beta_inc

  if ( x <= 0.0 ):
    cdf = 0.0
  elif ( x <= 1.0 ):
    cdf = beta_inc ( a, b, x )
  else:
    cdf = 1.0

  return cdf

def beta_cdf_inv ( cdf, p, q ):

#*****************************************************************************80
#
## BETA_CDF_INV computes inverse of the incomplete Beta function.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    04 March 2016
#
#  Author:
#
#    Original FORTRAN77 version by GW Cran, KJ Martin, GE Thomas.
#    Python version by John Burkardt.
#
#  Reference:
#
#    GW Cran, KJ Martin, GE Thomas,
#    Remark AS R19 and Algorithm AS 109:
#    A Remark on Algorithms AS 63: The Incomplete Beta Integral
#    and AS 64: Inverse of the Incomplete Beta Integeral,
#    Applied Statistics,
#    Volume 26, Number 1, 1977, pages 111-114.
#
#  Parameters:
#
#    Input, real P, Q, the parameters of the incomplete
#    Beta function.
#
#    Input, real CDF, the value of the incomplete Beta
#    function.  0 <= CDF <= 1.
#
#    Output, real VALUE, the argument of the Beta CDF which produces 
#    the value CDF.
#
#  Local Parameters:
#
#    Local, real ( kind = 8 ) SAE, the most negative decimal exponent
#    which does not cause an underflow.
#
  import numpy as np
  from beta_inc import beta_inc
  from r8_gamma import r8_gamma
  from sys import exit

  sae = -37.0

  fpu = 10.0 ** sae
#
#  Test for admissibility of parameters.
#
  if ( p <= 0.0 ):
    print ( '' )
    print ( 'BETA_CDF_INV - Fatal error!' )
    print ( '  P <= 0.' )
    exit ( 'BETA_CDF_INV - Fatal error!' )

  if ( q <= 0.0 ):
    print ( '' )
    print ( 'BETA_CDF_INV - Fatal error!' )
    print ( '  Q <= 0.' )
    exit ( 'BETA_CDF_INV - Fatal error!' )

  if ( cdf < 0.0 or 1.0 < cdf ):
    print ( '' )
    print ( 'BETA_CDF_INV - Fatal error!' )
    print ( '  CDF < 0 or 1 < CDF.' )
    exit ( 'BETA_CDF_INV - Fatal error!' )
#
#  If the value is easy to determine, return immediately.
#
  if ( cdf == 0.0 ):
    value = 0.0
    return value

  if ( cdf == 1.0 ):
    value = 1.0
    return value

  beta_log = np.log ( r8_gamma ( p ) ) + np.log ( r8_gamma ( q ) ) \
    - np.log ( r8_gamma ( p + q ) )
#
#  Change tail if necessary.
#
  if ( 0.5 < cdf ):
    a = 1.0 - cdf
    pp = q
    qq = p
    indx = 1
  else:
    a = cdf
    pp = p
    qq = q
    indx = 0
#
#  Calculate the initial approximation.
#
  r = np.sqrt ( - np.log ( a * a ) )

  y = r - ( 2.30753 + 0.27061 * r ) \
    / ( 1.0 + ( 0.99229 + 0.04481 * r ) * r )

  if ( 1.0 < pp and 1.0 < qq ):

    r = ( y * y - 3.0 ) / 6.0
    s = 1.0 / ( pp + pp - 1.0 )
    t = 1.0 / ( qq + qq - 1.0 )
    h = 2.0 / ( s + t )
    w = y * np.sqrt ( h + r ) / h - ( t - s ) \
      * ( r + 5.0 / 6.0 - 2.0 / ( 3.0 * h ) )
    value = pp / ( pp + qq * np.exp ( w + w ) )

  else:

    r = qq + qq
    t = 1.0 / ( 9.0 * qq )
    t = r * ( 1.0 - t + y * np.sqrt ( t ) ) ** 3

    if ( t <= 0.0 ):
      value = 1.0 - np.exp ( ( np.log ( ( 1.0 - a ) * qq ) + beta_log ) / qq )
    else:

      t = ( 4.0 * pp + r - 2.0 ) / t

      if ( t <= 1.0 ):
        value = np.exp ( ( np.log ( a * pp ) + beta_log ) / pp )
      else:
        value = 1.0 - 2.0 / ( t + 1.0 )
#
#  Solve for X by a modified Newton-Raphson method.
#
  r = 1.0 - pp
  t = 1.0 - qq
  yprev = 0.0
  sq = 1.0
  prev = 1.0

  if ( value < 0.0001 ):
    value = 0.0001

  if ( 0.9999 < value ):
    value = 0.9999

  iex = max ( - 5.0 / pp / pp - 1.0 / a ** 0.2 - 13.0, sae )

  acu = 10.0 ** iex

  while ( True ):

    y = beta_inc ( pp, qq, value )

    xin = value
    y = ( y - a ) * np.exp ( beta_log + r * np.log ( xin ) + t * np.log ( 1.0 - xin ) )

    if ( y * yprev <= 0.0 ):
      prev = max ( sq, fpu )

    g = 1.0

    while ( True ):

      while ( True ):

        adj = g * y
        sq = adj * adj

        if ( sq < prev ):

          tx = value - adj

          if ( 0.0 <= tx and tx <= 1.0 ):
            break

        g = g / 3.0

      if ( prev <= acu ):
        if ( indx ):
          value = 1.0 - value
        return value

      if ( y * y <= acu ):
        if ( indx ):
          value = 1.0 - value
        return value

      if ( tx != 0.0 and tx != 1.0 ):
        break

      g = g / 3.0

    if ( tx == value ):
      break
 
    value = tx
    yprev = y

  if ( indx ):
    value = 1.0 - value

  return value

def beta_cdf_test ( ):

#*****************************************************************************80
#
## BETA_CDF_TEST tests BETA_CDF, BETA_CDF_INV, BETA_PDF
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    04 March 2016
#
#  Author:
#
#    John Burkardt
#
  import platform

  print ( '' )
  print ( 'BETA_CDF_TEST' )
  print ( '  Python version: %s' % ( platform.python_version ( ) ) )
  print ( '  BETA_CDF evaluates the Beta CDF' )
  print ( '  BETA_CDF_INV inverts the Beta CDF.' )
  print ( '  BETA_PDF evaluates the Beta PDF' )

  a = 12.0
  b = 12.0

  print ( '' )
  print ( '  PDF parameter A = %14g' % ( a ) )
  print ( '  PDF parameter B = %14g' % ( b ) )

  check = beta_check ( a, b )

  if ( not check ):
    print ( '' )
    print ( 'BETA_CDF_TEST - Fatal error!' )
    print ( '  The parameters are not legal.' )
    return

  seed = 123456789

  print ( '' )
  print ( '        A               B               X               ' ),
  print ( 'PDF             CDF             CDF_INV' )
  print ( '' )

  for i in range ( 0, 10 ):

    x, seed = beta_sample ( a, b, seed )

    pdf = beta_pdf ( x, a, b )

    cdf = beta_cdf ( x, a, b )

    x2 = beta_cdf_inv ( cdf, a, b )

    print ( '%14g  %14g  %14g  %14g  %14g  %14g' % ( a, b, x, pdf, cdf, x2 ) )
#
#  Terminate.
#
  print ( '' )
  print ( 'BETA_CDF_TEST' )
  print ( '  Normal end of execution.' )
  return

def beta_check ( a, b ):

#*****************************************************************************80
#
## BETA_CHECK checks the parameters of the Beta PDF.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    04 March 2016
#
#  Author:
#
#    John Burkardt
#
#  Parameters:
#
#    Input, real A, B, the parameters of the PDF.
#    0.0 < A,
#    0.0 < B.
#
#    Output, logical CHECK, is TRUE if the parameters are legal.
#
  if ( a <= 0.0 ):
    print ( '' )
    print ( 'BETA_CHECK - Fatal error!' )
    print ( '  A <= 0.' )
    check = False
    return check

  if ( b <= 0.0 ):
    print ( '' )
    print ( 'BETA_CHECK - Fatal error!' )
    print ( '  B <= 0.' )
    check = False
    return check

  check = True

  return check

def beta_mean ( a, b ):

#*****************************************************************************80
#
## BETA_MEAN returns the mean of the Beta PDF.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    04 March 2016
#
#  Author:
#
#    John Burkardt
#
#  Parameters:
#
#    Input, real A, B, the parameters of the PDF.
#    0.0 < A,
#    0.0 < B.
#
#    Output, real MEAN, the mean of the PDF.
#
  mean = a / ( a + b )

  return mean

def beta_pdf ( x, a, b ):

#*****************************************************************************80
#
## BETA_PDF evaluates the Beta PDF.
#
#  Discussion:
#
#    PDF(X)(A,B) = X^(A-1) * (1-X)^(B-1) / BETA(A,B).
#
#    A = B = 1 yields the Uniform distribution on [0,1].
#    A = B = 1/2 yields the Arcsin distribution.
#        B = 1 yields the power function distribution.
#    A = B -> Infinity tends to the Normal distribution.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    04 March 2016
#
#  Author:
#
#    John Burkardt
#
#  Parameters:
#
#    Input, real X, the argument of the PDF.
#    0.0 <= X <= 1.0.
#
#    Input, real A, B, the parameters of the PDF.
#    0.0 < A,
#    0.0 < B.
#
#    Output, real PDF, the value of the PDF.
#
  from r8_beta import r8_beta

  if ( x < 0.0 or 1.0 < x ):
    pdf = 0.0
  else:
    pdf = x ** ( a - 1.0 ) * ( 1.0 - x ) ** ( b - 1.0 ) / r8_beta ( a, b )

  return pdf

def beta_sample ( a, b, seed ):

#*****************************************************************************80
#
## BETA_SAMPLE samples the Beta PDF.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    04 March 2016
#
#  Author:
#
#    John Burkardt
#
#  Reference:
#
#    William Kennedy and James Gentle,
#    Algorithm BN,
#    Statistical Computing,
#    Dekker, 1980.
#
#  Parameters:
#
#    Input, real A, B, the parameters of the PDF.
#    0.0 < A,
#    0.0 < B.
#
#    Input, integer SEED, a seed for the random number generator.
#
#    Output, real X, a sample of the PDF.
#
#    Output, integer SEED, an updated seed for the random number generator.
#
  import numpy as np
  from normal_01 import normal_01_sample
  from r8_uniform_01 import r8_uniform_01

  mu = ( a - 1.0 ) / ( a + b - 2.0 )
  stdev = 0.5 / np.sqrt ( a + b - 2.0 )

  while ( True ):

    y, seed = normal_01_sample ( seed )

    x = mu + stdev * y

    if ( x < 0.0 or 1.0 < x ):
      continue

    u, seed = r8_uniform_01 ( seed )

    test =     ( a - 1.0 )     * np.log (         x   / ( a - 1.0 ) ) \
             + ( b - 1.0 )     * np.log ( ( 1.0 - x ) / ( b - 1.0 ) ) \
             + ( a + b - 2.0 ) * np.log ( a + b - 2.0 ) + 0.5 * y ** 2

    if ( np.log ( u ) <= test ):
      break

  return x, seed

def beta_sample_test ( ):

#*****************************************************************************80
#
## BETA_SAMPLE_TEST tests BETA_MEAN, BETA_SAMPLE, BETA_VARIANCE.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    15 April 2009
#
#  Author:
#
#    John Burkardt
#
  import numpy as np
  import platform
  from r8vec_max import r8vec_max
  from r8vec_mean import r8vec_mean
  from r8vec_min import r8vec_min
  from r8vec_variance import r8vec_variance

  nsample = 1000
  seed = 123456789

  print ( '' )
  print ( 'BETA_SAMPLE_TEST' )
  print ( '  Python version: %s' % ( platform.python_version ( ) ) )
  print ( '  BETA_MEAN computes the Beta mean' )
  print ( '  BETA_SAMPLE samples the Beta distribution' )
  print ( '  BETA_VARIANCE computes the Beta variance.' )

  a = 2.0
  b = 3.0

  check = beta_check ( a, b )

  if ( not check ):
    print ( '' )
    print ( 'BETA_SAMPLE_TEST - Fatal error!' )
    print ( '  The parameters are not legal.' )
    return

  mean = beta_mean ( a, b )
  variance = beta_variance ( a, b )

  print ( '' )
  print ( '  PDF parameter A = %14g' % ( a ) )
  print ( '  PDF parameter B = %14g' % ( b ) )
  print ( '  PDF mean =        %14g' % ( mean ) )
  print ( '  PDF variance =    %14g' % ( variance ) )

  x = np.zeros ( nsample )
  for i in range ( 0, nsample ):
    x[i], seed = beta_sample ( a, b, seed )

  mean = r8vec_mean ( nsample, x )
  variance = r8vec_variance ( nsample, x )
  xmax = r8vec_max ( nsample, x )
  xmin = r8vec_min ( nsample, x )

  print ( '' )
  print ( '  Sample size =     %6d' % ( nsample ) )
  print ( '  Sample mean =     %14g' % ( mean ) )
  print ( '  Sample variance = %14g' % ( variance ) )
  print ( '  Sample maximum =  %14g' % ( xmax ) )
  print ( '  Sample minimum =  %14g' % ( xmin ) )
#
#  Terminate.
#
  print ( '' )
  print ( 'BETA_SAMPLE_TEST' )
  print ( '  Normal end of execution.' )
  return

def beta_variance ( a, b ):

#*****************************************************************************80
#
## BETA_VARIANCE returns the variance of the Beta PDF.
#
#  Licensing:
#
#    This code is distributed under the GNU LGPL license.
#
#  Modified:
#
#    03 September 2004
#
#  Author:
#
#    John Burkardt
#
#  Parameters:
#
#    Input, real A, B, the parameters of the PDF.
#    0.0 < A,
#    0.0 < B.
#
#    Output, real VARIANCE, the variance of the PDF.
#
  variance = ( a * b ) / ( ( a + b ) ** 2 * ( 1.0 + a + b ) )

  return variance

if ( __name__ == '__main__' ):
  from timestamp import timestamp
  timestamp ( )
  beta_cdf_test ( )
  beta_sample_test ( )
  timestamp ( )

